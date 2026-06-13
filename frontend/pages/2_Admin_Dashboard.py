"""
AI Resume Analyzer — Admin Dashboard

Manage jobs, run scoring, view shortlist, and trigger emails.
Premium dark theme with glassmorphism design.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils import (
    api_get, api_post, api_put, api_delete,
    is_logged_in, is_admin, get_user, logout,
)
from frontend.styles import get_global_css

st.set_page_config(page_title="Admin Dashboard — AI Resume Analyzer", page_icon="👔", layout="wide")

# ── Inject Global CSS ──
st.markdown(get_global_css(), unsafe_allow_html=True)

# ── Auth check ──
if not is_logged_in():
    st.warning("🔒 Please log in first from the main page.")
    st.stop()

if not is_admin():
    st.warning("⛔ Admin access required. Please log in with an admin account.")
    st.stop()

# ── Sidebar ──
with st.sidebar:
    st.markdown("### 👔 Admin Dashboard")
    st.markdown("---")
    user = get_user()
    st.markdown(f"**👤 {user.get('username', 'Admin')}**")
    st.caption("Role: Admin / Recruiter")
    st.markdown("---")

    # System status
    st.markdown("#### ⚙️ System Status")
    try:
        health = api_get("/health")
        if health:
            llm_status = health.get("llm_enabled", False)
            if llm_status:
                st.markdown("🤖 LLM Extraction: **Active** ✅")
            else:
                st.markdown("🤖 LLM Extraction: **Off** ⚠️")
            st.markdown(f"📧 Email Mode: **{'Dev (File)' if True else 'SMTP'}**")
    except Exception:
        st.caption("Unable to fetch system status")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()



# ── Header ──
st.markdown("""
<div class="hero-header" style="background:linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,41,59,0.95));">
    <h1>👔 Admin Dashboard</h1>
    <p>Manage jobs, score candidates, and automate email communications</p>
</div>
""", unsafe_allow_html=True)

tab_jobs, tab_candidates, tab_scoring, tab_emails = st.tabs([
    "💼 Jobs", "👥 Candidates", "🎯 Scoring & Shortlist", "📧 Emails"
])


# ═══════════════════════════════════════════
# TAB: Jobs
# ═══════════════════════════════════════════
with tab_jobs:
    col_list, col_create = st.columns([2, 1])

    with col_create:
        st.markdown("#### ➕ Create New Job")

        with st.form("create_job_form"):
            title = st.text_input("Job Title", placeholder="e.g. Senior Python Developer", help="The title candidates will see when browsing positions")
            description = st.text_area(
                "Job Description",
                placeholder="Full job description with responsibilities and requirements...",
                height=200,
                help="Include key responsibilities, qualifications, and what you're looking for",
            )
            required_skills_str = st.text_input(
                "Required Skills (comma-separated)",
                placeholder="Python, FastAPI, SQL, Docker",
                help="These skills will be weighted heavily in scoring",
            )
            preferred_skills_str = st.text_input(
                "Preferred Skills (comma-separated)",
                placeholder="AWS, Kubernetes, React",
                help="Nice-to-have skills that boost candidate scores",
            )
            experience_level = st.selectbox(
                "Experience Level",
                [None, "junior", "mid", "senior"],
                format_func=lambda x: "🔵 Any Level" if x is None else {"junior": "🟢 Junior (0-2 years)", "mid": "🟡 Mid-Level (3-5 years)", "senior": "🔴 Senior (5+ years)"}[x],
            )

            submitted = st.form_submit_button("Create Job", use_container_width=True, type="primary")

            if submitted:
                if not title:
                    st.warning("⚠️ Please provide a job title")
                elif not description or len(description) < 10:
                    st.warning("⚠️ Please provide a detailed description (min 10 chars)")
                else:
                    req_skills = [s.strip() for s in required_skills_str.split(",") if s.strip()] if required_skills_str else []
                    pref_skills = [s.strip() for s in preferred_skills_str.split(",") if s.strip()] if preferred_skills_str else []

                    result = api_post("/jobs/", {
                        "title": title,
                        "description": description,
                        "required_skills": req_skills,
                        "preferred_skills": pref_skills,
                        "experience_level": experience_level,
                    })

                    if result:
                        st.success(f"✅ Job '{title}' created successfully! (ID: {result['id']})")
                        st.rerun()

    with col_list:
        st.markdown("#### 📋 Existing Jobs")

        jobs = api_get("/jobs/")
        if jobs:
            for job in jobs:
                status_label = "🟢 Active" if job["status"] == "active" else "🔴 Closed"

                with st.expander(f"{'💼' if job['status'] == 'active' else '🔒'} {job['title']} — {status_label}"):
                    st.markdown(f"**ID:** {job['id']} · **Created:** {job.get('created_at', '')[:10]}")
                    st.markdown(f"**Description:** {job.get('description', '')[:300]}...")

                    req = job.get("required_skills") or []
                    pref = job.get("preferred_skills") or []
                    if req:
                        req_html = " ".join(
                            f'<span style="display:inline-block;background:rgba(239,68,68,0.1);color:#f87171;padding:3px 10px;border-radius:16px;margin:2px;font-size:0.8rem;border:1px solid rgba(239,68,68,0.2);">{s}</span>'
                            for s in req
                        )
                        st.markdown(f"**Required:** {req_html}", unsafe_allow_html=True)
                    if pref:
                        pref_html = " ".join(
                            f'<span style="display:inline-block;background:rgba(34,197,94,0.1);color:#4ade80;padding:3px 10px;border-radius:16px;margin:2px;font-size:0.8rem;border:1px solid rgba(34,197,94,0.2);">{s}</span>'
                            for s in pref
                        )
                        st.markdown(f"**Preferred:** {pref_html}", unsafe_allow_html=True)

                    if job.get("experience_level"):
                        st.markdown(f"**Level:** {job['experience_level'].title()}")

                    if job["status"] == "active":
                        if st.button(f"🔒 Close Job", key=f"close_{job['id']}"):
                            api_delete(f"/jobs/{job['id']}")
                            st.rerun()
        else:
            st.markdown("""
            <div class="glass-card" style="text-align:center;padding:2rem;">
                <span style="font-size:2.5rem;">💼</span>
                <p style="color:#94a3b8;margin-top:1rem;">No jobs created yet. Use the form on the right to create one.</p>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════
# TAB: Candidates
# ═══════════════════════════════════════════
with tab_candidates:
    st.markdown("#### 👥 All Candidates")

    if st.button("🔄 Refresh", key="refresh_candidates"):
        st.rerun()

    candidates = api_get("/candidates/")

    if candidates:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Total Candidates", len(candidates))
        with col2:
            with_skills = sum(1 for c in candidates if c.get("skills_count", 0) > 0)
            st.metric("🛠️ With Parsed Skills", with_skills)
        with col3:
            with_resume = sum(1 for c in candidates if c.get("resume_count", 0) > 0)
            st.metric("📄 With Resumes", with_resume)

        st.markdown("---")

        for candidate in candidates:
            skills_count = candidate.get('skills_count', 0)
            resume_count = candidate.get('resume_count', 0)
            status_dot = "🟢" if skills_count > 0 else "🟡"

            with st.expander(f"{status_dot} {candidate['full_name']} — {candidate['email']}"):
                col_info, col_stats = st.columns([2, 1])
                with col_info:
                    st.markdown(f"**ID:** {candidate['id']}")
                    st.markdown(f"**Joined:** {candidate.get('created_at', '')[:10]}")
                with col_stats:
                    st.markdown(f"**Skills:** {skills_count} · **Resumes:** {resume_count}")

                # View full details
                if st.button(f"🔍 View Details", key=f"detail_{candidate['id']}"):
                    detail = api_get(f"/candidates/{candidate['id']}")
                    if detail:
                        skills = detail.get("extracted_skills") or []
                        if skills:
                            skill_html = " ".join(
                                f'<span style="display:inline-block;background:rgba(124,58,237,0.15);color:#c4b5fd;padding:3px 10px;border-radius:16px;margin:2px;font-size:0.8rem;border:1px solid rgba(124,58,237,0.3);">{s}</span>'
                                for s in skills
                            )
                            st.markdown(f"**Skills:** {skill_html}", unsafe_allow_html=True)

                        exp = detail.get("extracted_experience") or {}
                        if isinstance(exp, dict) and exp.get("total_years"):
                            st.markdown(f"**Experience:** {exp['total_years']} years")

                        edu = detail.get("extracted_education") or []
                        if edu:
                            st.markdown("**Education:** " + " · ".join(
                                e.get("description", e.get("degree", ""))
                                for e in edu if isinstance(e, dict)
                            ))
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:3rem;">
            <span style="font-size:3rem;">👥</span>
            <p style="color:#94a3b8;font-size:1.1rem;margin-top:1rem;">No candidates registered yet</p>
            <p style="color:#64748b;">Candidates will appear here once they register and upload resumes</p>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════
# TAB: Scoring & Shortlist
# ═══════════════════════════════════════════
with tab_scoring:
    st.markdown("#### 🎯 AI-Powered Scoring")
    st.caption("Score candidates against job requirements using keyword matching, semantic embeddings, and rule-based analysis")

    jobs = api_get("/jobs/", params={"status": "active"})

    if not jobs:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:2rem;">
            <span style="font-size:2.5rem;">💼</span>
            <p style="color:#94a3b8;">No active jobs. Create a job first in the Jobs tab.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        selected_job = st.selectbox(
            "Select Job to Score Against",
            jobs,
            format_func=lambda j: f"{j['title']} (ID: {j['id']})",
            help="Choose which job posting to score candidates against",
        )

        col_run, col_view = st.columns(2)

        with col_run:
            if st.button("🚀 Run Scoring Now", type="primary", use_container_width=True):
                with st.spinner("🤖 Running AI-powered scoring... Analyzing skills, experience, and semantic similarity. This may take a moment."):
                    results = api_post("/scoring/run", {"job_id": selected_job["id"]})

                    if results:
                        st.success(
                            f"✅ Scored **{results['total_candidates']}** candidates · "
                            f"**{results['shortlisted_count']}** shortlisted!"
                        )
                        st.session_state["last_scoring_results"] = results

        with col_view:
            if st.button("📊 View Existing Results", use_container_width=True):
                results = api_get(f"/scoring/results/{selected_job['id']}")
                if results:
                    st.session_state["last_scoring_results"] = results

        # Display results
        results = st.session_state.get("last_scoring_results")
        if results and results.get("results"):
            st.markdown("---")
            st.markdown(f"### 📊 Results: {results['job_title']}")

            # Summary metrics
            total = results["total_candidates"]
            shortlisted = results["shortlisted_count"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Scored", total)
            with col2:
                st.metric("✅ Shortlisted", shortlisted)
            with col3:
                rate = (shortlisted / total * 100) if total > 0 else 0
                st.metric("📈 Shortlist Rate", f"{rate:.0f}%")

            st.markdown("---")

            # Results table
            for item in results["results"]:
                score_pct = item["overall_score"] * 100
                is_shortlisted = item.get("shortlisted", False)

                if is_shortlisted:
                    badge = '<span class="badge-success">✅ SHORTLISTED</span>'
                    icon = "🟢"
                else:
                    badge = '<span class="badge-danger">❌ NOT SHORTLISTED</span>'
                    icon = "🔴"

                with st.expander(f"{icon} #{item['rank']} · {item['candidate_name']} — {score_pct:.1f}%"):
                    st.markdown(f"**📧 Email:** {item['candidate_email']} {badge}", unsafe_allow_html=True)
                    st.progress(min(item["overall_score"], 1.0))

                    # Score explanation
                    if item.get("explanation"):
                        st.markdown("**📝 Score Breakdown:**")
                        for part in item["explanation"].split(" | "):
                            st.markdown(f"  - {part}")

                    # Skill match details
                    skill_detail = item.get("skill_match_detail") or []
                    if skill_detail:
                        matched = [s for s in skill_detail if s.get("matched")]
                        unmatched = [s for s in skill_detail if not s.get("matched")]

                        if matched:
                            matched_html = " ".join(
                                f'<span style="display:inline-block;background:rgba(34,197,94,0.1);color:#4ade80;padding:3px 10px;border-radius:16px;margin:2px;font-size:0.8rem;border:1px solid rgba(34,197,94,0.2);">{s["skill"]} ({s.get("confidence", 0):.0%})</span>'
                                for s in matched
                            )
                            st.markdown(f"**✅ Matched:** {matched_html}", unsafe_allow_html=True)
                        if unmatched:
                            unmatched_html = " ".join(
                                f'<span style="display:inline-block;background:rgba(239,68,68,0.1);color:#f87171;padding:3px 10px;border-radius:16px;margin:2px;font-size:0.8rem;border:1px solid rgba(239,68,68,0.2);">{s["skill"]}</span>'
                                for s in unmatched
                            )
                            st.markdown(f"**❌ Missing:** {unmatched_html}", unsafe_allow_html=True)

            # Store shortlisted IDs for email tab
            st.session_state["shortlisted_ids"] = [
                item["candidate_id"] for item in results["results"] if item.get("shortlisted")
            ]
            st.session_state["all_candidate_ids"] = [
                item["candidate_id"] for item in results["results"]
            ]
            st.session_state["scoring_job_id"] = results["job_id"]


# ═══════════════════════════════════════════
# TAB: Emails
# ═══════════════════════════════════════════
with tab_emails:
    st.markdown("#### 📧 Email Automation")
    st.caption("Send professional notification emails to candidates with one click")

    subtab_send, subtab_logs = st.tabs(["✉️ Send Emails", "📜 Email History"])

    with subtab_send:
        job_id = st.session_state.get("scoring_job_id")
        shortlisted_ids = st.session_state.get("shortlisted_ids", [])
        all_ids = st.session_state.get("all_candidate_ids", [])

        if not job_id:
            st.markdown("""
            <div class="glass-card" style="text-align:center;padding:2.5rem;">
                <span style="font-size:2.5rem;">🎯</span>
                <p style="color:#94a3b8;font-size:1.1rem;margin-top:1rem;">Run scoring first</p>
                <p style="color:#64748b;">Go to the <strong>Scoring & Shortlist</strong> tab to score candidates before sending emails</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom:1rem;">
                <h3>📋 Email Configuration</h3>
                <p style="color:#e2e8f0;"><strong>Job ID:</strong> {job_id} · <strong>Shortlisted:</strong> {len(shortlisted_ids)} · <strong>Total:</strong> {len(all_ids)}</p>
            </div>
            """, unsafe_allow_html=True)

            template = st.selectbox(
                "Email Template",
                ["shortlist", "rejection"],
                format_func=lambda x: "🎉 Shortlist Notification — Congratulations email" if x == "shortlist" else "📋 Rejection Notification — Professional follow-up",
                help="Choose the type of email to send. Shortlist goes to selected candidates, rejection to the rest.",
            )

            if template == "shortlist":
                target_ids = shortlisted_ids
                st.success(f"✅ Will send **shortlist** emails to **{len(target_ids)}** shortlisted candidates")
            else:
                non_shortlisted = [cid for cid in all_ids if cid not in shortlisted_ids]
                target_ids = non_shortlisted
                st.info(f"📋 Will send **rejection** emails to **{len(target_ids)}** non-shortlisted candidates")

            custom_msg = st.text_area(
                "Custom Message (optional)",
                placeholder="Add a personal note from the hiring team...",
                height=100,
                help="This message will be included in the email template. Leave empty for the default message.",
            )

            if target_ids:
                st.markdown("---")
                if st.button("📤 Send Emails", type="primary", use_container_width=True):
                    with st.spinner(f"📧 Sending {template} emails to {len(target_ids)} candidates..."):
                        result = api_post("/emails/send", {
                            "candidate_ids": target_ids,
                            "job_id": job_id,
                            "template": template,
                            "custom_message": custom_msg,
                        })

                        if result:
                            total = result.get("total", 0)
                            sent = result.get("sent", 0)
                            failed = result.get("failed", 0)

                            if failed == 0:
                                st.success(f"✅ All {sent} emails sent successfully!")
                                st.balloons()
                            elif sent == 0:
                                st.error(f"❌ All {failed} emails failed to send")
                            else:
                                st.warning(f"⚠️ Partial success: {sent} sent, {failed} failed out of {total}")

                            if result.get("details"):
                                st.markdown("---")
                                st.markdown("**📋 Details:**")
                                for detail in result["details"]:
                                    if detail["status"] == "sent":
                                        st.markdown(f"✅ **{detail['recipient_email']}** — Sent successfully")
                                    else:
                                        err = f" ({detail['error_message']})" if detail.get("error_message") else ""
                                        st.markdown(f"❌ **{detail['recipient_email']}** — Failed{err}")
            else:
                st.warning("⚠️ No candidates to email for this selection. Run scoring first or change the template.")

    with subtab_logs:
        st.markdown("#### 📜 Email Send History")
        st.caption("View all previously sent emails and their status")

        if st.button("🔄 Refresh Logs", key="refresh_logs"):
            st.rerun()

        logs = api_get("/emails/logs")

        if logs:
            for log in logs:
                status_icon = {"sent": "✅", "failed": "❌", "queued": "⏳"}.get(log["status"], "❓")
                template_badge = "🎉" if log["template_name"] == "shortlist" else "📋"
                st.markdown(
                    f"{status_icon} **{log['recipient_email']}** — "
                    f"{template_badge} `{log['template_name']}` — {log['subject'][:50]}... "
                    f"({log.get('sent_at', 'pending')[:19] if log.get('sent_at') else 'pending'})"
                )
                if log.get("error_message"):
                    st.caption(f"⚠️ Error: {log['error_message']}")
        else:
            st.markdown("""
            <div class="glass-card" style="text-align:center;padding:2rem;">
                <span style="font-size:2.5rem;">📧</span>
                <p style="color:#94a3b8;">No email logs yet. Send some emails to see history here.</p>
            </div>
            """, unsafe_allow_html=True)
