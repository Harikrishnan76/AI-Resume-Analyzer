"""
AI Resume Analyzer — Email Service

Handles email sending with Jinja2 template rendering.
Supports:
1. Resend API (HTTP-based, highly reliable)
2. SendGrid API (HTTP-based, highly reliable)
3. SMTP (Standard with secure TLS handshake, proper multi-part headers)
4. Dev Mode (Saves mock emails to files and reports success)
"""

import logging
import smtplib
from datetime import datetime, timezone
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Optional
import httpx

from jinja2 import Environment, FileSystemLoader

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Template engine ──
_template_dir = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_template_dir)),
    autoescape=True,
)


def render_template(template_name: str, context: dict) -> str:
    """Render an HTML email template with the given context."""
    try:
        template = _jinja_env.get_template(f"{template_name}_email.html")
        return template.render(**context)
    except Exception as e:
        logger.error("Failed to render template %s: %s", template_name, e)
        # Fallback to plain text
        return _plain_text_fallback(template_name, context)


def _plain_text_fallback(template_name: str, context: dict) -> str:
    """Generate plain text email when template rendering fails."""
    candidate_name = context.get("candidate_name", "Candidate")
    job_title = context.get("job_title", "the position")
    company = context.get("company_name", "Our Company")

    if template_name == "shortlist":
        return (
            f"Dear {candidate_name},\n\n"
            f"Congratulations! We are pleased to inform you that your application "
            f"for {job_title} at {company} has been shortlisted.\n\n"
            f"We will be in touch soon with next steps.\n\n"
            f"Best regards,\n{company} Recruiting Team"
        )
    else:
        return (
            f"Dear {candidate_name},\n\n"
            f"Thank you for your interest in {job_title} at {company}. "
            f"After careful review, we have decided to move forward with other candidates.\n\n"
            f"We appreciate the time you invested and encourage you to apply for future openings.\n\n"
            f"Best regards,\n{company} Recruiting Team"
        )


def _save_email_to_file(to_email: str, subject: str, html_body: str) -> dict:
    """
    Save email as an HTML file in data/sent_emails/.
    Used in dev mode as a reliable alternative to SMTP.
    Returns success dict with file path.
    """
    try:
        sent_emails_dir = Path("data/sent_emails")
        sent_emails_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_email = to_email.replace('@', '_at_').replace('.', '_')
        filename = f"{timestamp}_{safe_email}.html"
        filepath = sent_emails_dir / filename

        # Wrap with metadata header for easy viewing
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{subject}</title>
    <style>
        .email-meta {{
            background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;
            padding: 16px; margin-bottom: 20px; font-family: Arial, sans-serif;
        }}
        .email-meta strong {{ color: #0369a1; }}
    </style>
</head>
<body>
    <div class="email-meta">
        <strong>📧 Email Preview (Dev Mode)</strong><br>
        <strong>To:</strong> {to_email}<br>
        <strong>Subject:</strong> {subject}<br>
        <strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
    </div>
    {html_body}
</body>
</html>"""

        filepath.write_text(full_html, encoding="utf-8")
        logger.info("📧 [DEV MODE] Email saved to %s", filepath)

        return {
            "success": True,
            "error": None,
            "dev_mode": True,
            "file_path": str(filepath),
        }
    except Exception as file_err:
        logger.error("Failed to save dev email file: %s", file_err)
        return {
            "success": False,
            "error": f"Dev mode file save failed: {file_err}",
        }


def _send_via_resend(to_email: str, subject: str, html_body: str, text_body: str, sender: str) -> dict:
    """Send email using Resend API."""
    try:
        logger.info("Sending email to %s via Resend API...", to_email)
        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": sender if "@" in sender and not sender.endswith(".local") else "onboarding@resend.dev",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        }
        resp = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=15.0)
        if resp.status_code in (200, 201):
            logger.info("Email sent to %s successfully via Resend", to_email)
            return {"success": True, "error": None}
        else:
            err_msg = f"Resend API error ({resp.status_code}): {resp.text}"
            logger.error(err_msg)
            return {"success": False, "error": err_msg}
    except Exception as e:
        logger.error("Resend delivery failed: %s", e)
        return {"success": False, "error": str(e)}


def _send_via_sendgrid(to_email: str, subject: str, html_body: str, text_body: str, sender: str) -> dict:
    """Send email using SendGrid API."""
    try:
        logger.info("Sending email to %s via SendGrid API...", to_email)
        headers = {
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": sender if "@" in sender and not sender.endswith(".local") else "noreply@resumeanalyzer.local"},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_body},
                {"type": "text/html", "value": html_body}
            ]
        }
        resp = httpx.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers, timeout=15.0)
        if resp.status_code in (200, 201, 202):
            logger.info("Email sent to %s successfully via SendGrid", to_email)
            return {"success": True, "error": None}
        else:
            err_msg = f"SendGrid API error ({resp.status_code}): {resp.text}"
            logger.error(err_msg)
            return {"success": False, "error": err_msg}
    except Exception as e:
        logger.error("SendGrid delivery failed: %s", e)
        return {"success": False, "error": str(e)}


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    from_email: Optional[str] = None,
) -> dict:
    """
    Send an email via configured channels (Resend, SendGrid, SMTP, or Dev Mode file save).
    Ensures optimal success rates by utilizing full headers, plain text fallbacks, 
    and proper SMTP ehlo handshaking.
    """
    sender = from_email or settings.smtp_from_email
    fallback_text = text_body or "Please view this email in an HTML-compatible email client."

    # ── 1. Dev mode: save to file directly (no network calls) ──
    if settings.email_dev_mode:
        logger.info("📧 Dev mode active — saving email to file instead of network send")
        return _save_email_to_file(to_email, subject, html_body)

    # ── 2. Modern HTTP APIs (Resend / SendGrid) ──
    if settings.resend_api_key:
        return _send_via_resend(to_email, subject, html_body, fallback_text, sender)
    
    if settings.sendgrid_api_key:
        return _send_via_sendgrid(to_email, subject, html_body, fallback_text, sender)

    # ── 3. Production SMTP flow with enhanced headers and handshake ──
    msg = MIMEMultipart("alternative")
    
    # Secure Header Encoding (crucial for subjects containing Emojis like 🎉)
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = sender
    msg["To"] = to_email
    
    # Spam Prevention Headers (standard RFC compliance)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=settings.smtp_host)

    # Attach multipart options (Text + HTML) for low spam scores
    msg.attach(MIMEText(fallback_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=12.0)
            server.ehlo()
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12.0)
            # Identify our client to the mail server first
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                # Re-negotiate capabilities over the TLS channel
                server.ehlo()

        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)

        server.sendmail(sender, [to_email], msg.as_string())
        server.quit()

        logger.info("SMTP Email sent to %s: %s", to_email, subject)
        return {"success": True, "error": None}

    except Exception as e:
        error_msg = f"SMTP failed ({e})"
        logger.warning("%s. Saving fallback draft to data/sent_emails/", error_msg)

        # Fallback: save to file
        fallback = _save_email_to_file(to_email, subject, html_body)
        if fallback["success"]:
            return {
                "success": False,
                "error": f"{error_msg} — Email saved as draft to {fallback.get('file_path', 'data/sent_emails/')}",
            }
        return {"success": False, "error": error_msg}


def send_candidate_email(
    template_name: str,
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    custom_message: str = "",
    score: Optional[float] = None,
) -> dict:
    """
    High-level function to send a templated email to a candidate.
    """
    context = {
        "candidate_name": candidate_name,
        "job_title": job_title,
        "company_name": settings.app_name.replace("AI ", "").replace(" Analyzer", " Co."),
        "custom_message": custom_message,
        "score": round(score * 100, 1) if score else None,
        "year": datetime.now().year,
    }

    html_body = render_template(template_name, context)
    text_body = _plain_text_fallback(template_name, context)

    if template_name == "shortlist":
        subject = f"🎉 Great News — You've Been Shortlisted for {job_title}!"
    else:
        subject = f"Application Update — {job_title}"

    result = send_email(
        to_email=candidate_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )

    return {
        **result,
        "recipient": candidate_email,
        "subject": subject,
        "template": template_name,
        "sent_at": datetime.now(timezone.utc) if result["success"] else None,
    }
