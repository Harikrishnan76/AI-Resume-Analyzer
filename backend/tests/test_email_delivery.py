"""
Test script for verifying SMTP & API mail send configuration.
"""
from backend.services.email_service import send_email
from backend.config import settings

def run_tests():
    print("=== Testing Email Configurations ===")
    print(f"SMTP Host:      {settings.smtp_host}")
    print(f"SMTP Port:      {settings.smtp_port}")
    print(f"Email Dev Mode: {settings.email_dev_mode}")
    print(f"Resend Key:     {settings.resend_api_key[:10] + '...' if settings.resend_api_key else 'None'}")
    print(f"SendGrid Key:   {settings.sendgrid_api_key[:10] + '...' if settings.sendgrid_api_key else 'None'}")
    
    # Run a test email save (dev mode) or send
    res = send_email(
        to_email="test@candidate.com",
        subject="🎉 Test Shortlist Email",
        html_body="<p>This is a test HTML body.</p>",
        text_body="This is a test plain text body."
    )
    
    print("\nResult status:", res)

if __name__ == "__main__":
    run_tests()
