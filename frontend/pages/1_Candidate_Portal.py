"""
AI Resume Analyzer — Candidate Portal

Upload resumes, view parsed profile data, and check scores.
Premium dark theme with glassmorphism design.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils import (
    api_get, api_post, is_logged_in, is_admin, get_user, logout
)
from frontend.styles import get_global_css

st.set_page_config(page_title="Candidate Portal — AI Resume Analyzer", page_icon="📋", layout="wide")

# ── Inject Global CSS ──
st.markdown(get_global_css(), unsafe_allow_html=True)

# ── Auth check ──
if not is_logged_in():
    st.warning("🔒 Please log in first from the main page.")
    st.stop()

if is_admin():
    st.info("👔 You're logged in as an admin. Switch to the **Admin Dashboard** for management features.")
    st.stop()

# ── Sidebar ──
with st.sidebar:
    st.markdown("### 📋 Candidate Portal")
    st.markdown("---")
    user = get_user()
    st.markdown(f"**👤 {user.get('username', 'User')}**")
    st.caption(f"📧 {user.get('email', '')}")
    st.markdown("---")
    st.markdown("""
    #### 📖 Quick Tips
    - Upload **PDF** or **DOCX** format
    - Max file size: **10 MB**
    - AI extracts skills automatically
    - Check **My Profile** for results
    """)
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

# ── Header ──
st.markdown("""
<div class="hero-header">
    <h1>📋 Candidate Portal</h1>
    <p>Upload your resume and view your AI-powered profile analysis</p>
</div>
""", unsafe_allow_html=True)

tab_upload, tab_profile, tab_jobs = st.tabs(["📤 Upload Resume", "👤 My Profile", "💼 Open Jobs"])

# ═══════════════════════════════════════════
# TAB: Upload Resume
# ═══════════════════════════════════════════
with tab_upload:
    st.subheader("📤 Upload Your Resume")
    st.markdown("Upload a **PDF** or **DOCX** file. Our AI will extract your skills, experience, and education using advanced NLP.")

    uploaded_file = st.file_uploader(
        "Choose your resume file",
        type=["pdf", "docx"],
        help="Supported formats: PDF, DOCX. Maximum size: 10MB. Your resume will be analyzed using AI-powered extraction.",
    )

    if uploaded_file:
        # File info card
        file_size_kb = uploaded_file.size / 1024
        file_type_icon = "📕" if uploaded_file.name.endswith('.pdf') else "📘"
        st.markdown(f"""
        <div class="glass-card" style="margin:1rem 0;">
            <div style="display:flex;align-items:center;gap:16px;">
                <span style="font-size:2.5rem;">{file_type_icon}</span>
                <div>
                    <strong style="color:#e2e8f0;font-size:1.1rem;">{uploaded_file.name}</strong><br>
                    <span style="color:#94a3b8;">Size: {file_size_kb:.1f} KB · Type: {uploaded_file.type}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Upload & Analyze", type="primary", use_container_width=True):
            with st.spinner("🔄 Uploading and analyzing your resume... Our AI is extracting skills, experience, and education. This may take a moment."):
                # Upload via API
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                result = api_post("/candidates/upload", files=files)

                if result:
                    st.success("✅ Resume uploaded and analyzed successfully!")
                    st.balloons()

                    # Show resume record in a nice card
                    parse_status = result.get("parse_status", "unknown")
                    status_color = "#4ade80" if parse_status == "parsed" else "#f87171"
                    st.markdown(f"""
                    <div class="glass-card" style="margin-top:1rem;">
                        <h3>📊 Analysis Result</h3>
                        <p style="color:#e2e8f0;"><strong>Resume ID:</strong> {result.get("id")}</p>
                        <p style="color:#e2e8f0;"><strong>File:</strong> {result.get("filename")}</p>
                        <p style="color:#e2e8f0;"><strong>Status:</strong> <span style="color:{status_color};font-weight:600;">{parse_status.upper()}</span></p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.info("💡 **Tip:** Go to the **My Profile** tab to see your extracted skills, experience, and education.")
                else:
                    st.error("❌ Upload failed. Please check the file format and try again.")
    else:
        # Empty state
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:3rem;">
            <span style="font-size:3rem;">📄</span>
            <p style="color:#94a3b8;margin-top:1rem;">Drag and drop your resume above, or click to browse</p>
            <p style="color:#64748b;font-size:0.85rem;">Supported: PDF, DOCX · Max 10MB</p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════
# TAB: My Profile
# ═══════════════════════════════════════════
with tab_profile:
    st.subheader("👤 Your Parsed Profile")

    if st.button("🔄 Refresh Profile", key="refresh_profile"):
        st.rerun()

    profile = api_get("/candidates/me")

    if profile:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"""
            <div class="glass-card">
                <h3 style="color:#c4b5fd;font-size:0.8rem;margin:0 0 1rem;">PERSONAL INFO</h3>
                <p style="color:#f1f5f9;font-size:1.3rem;font-weight:700;margin:0;">👤 {profile.get('full_name', 'N/A')}</p>
                <p style="color:#94a3b8;margin:0.5rem 0 0;">📧 {profile.get('email', 'N/A')}</p>
                <p style="color:#94a3b8;margin:0.25rem 0 0;">📱 {profile.get('phone') or 'Not extracted'}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            skills = profile.get("extracted_skills") or []
            if skills:
                st.markdown("**🛠️ Extracted Skills:**")
                # Display skills as styled tags
                skill_html = " ".join(
                    f'<span style="display:inline-block;background:rgba(124,58,237,0.15);color:#c4b5fd;padding:5px 14px;border-radius:20px;margin:4px;font-size:0.85rem;font-weight:500;border:1px solid rgba(124,58,237,0.3);transition:all 0.2s;">{s}</span>'
                    for s in skills
                )
                st.markdown(f'<div style="line-height:2.4;">{skill_html}</div>', unsafe_allow_html=True)
                st.caption(f"📊 {len(skills)} skills detected")
            else:
                st.markdown("""
                <div class="glass-card" style="text-align:center;padding:2rem;">
                    <span style="font-size:2rem;">🛠️</span>
                    <p style="color:#94a3b8;">No skills extracted yet. Upload your resume first!</p>
                </div>
                """, unsafe_allow_html=True)

        # Experience
        st.markdown("---")
        experience = profile.get("extracted_experience") or {}
        if isinstance(experience, dict):
            total_years = experience.get("total_years", 0)
            entries = experience.get("entries", [])

            st.markdown(f"**💼 Experience** — {total_years} year(s)")
            if entries:
                for entry in entries[:5]:
                    if isinstance(entry, dict):
                        title = entry.get("title", entry.get("description", ""))
                        company = entry.get("company", "")
                        period = entry.get("period", "")
                        highlights = entry.get("highlights", [])
                        st.markdown(f"- **{title}** {f'at _{company}_' if company else ''} ({period})")
                        if highlights and isinstance(highlights, list):
                            for h in highlights[:3]:
                                st.caption(f"  → {h}")
            else:
                st.caption("No detailed experience entries extracted. Try uploading a more detailed resume.")
        else:
            st.caption("No experience data available.")

        # Education
        education = profile.get("extracted_education") or []
        if education:
            st.markdown("**🎓 Education:**")
            for edu in education[:5]:
                if isinstance(edu, dict):
                    desc = edu.get("description", edu.get("degree", ""))
                    level = edu.get("level", "")
                    institution = edu.get("institution", "")
                    level_colors = {"doctorate": "#a855f7", "masters": "#6366f1", "bachelors": "#22c55e", "associate": "#3b82f6", "certification": "#f59e0b"}
                    badge_color = level_colors.get(level, "#64748b")
                    st.markdown(
                        f'- {desc} {f"· _{institution}_" if institution else ""} '
                        f'<span style="background:rgba({",".join(str(int(badge_color.lstrip("#")[i:i+2], 16)) for i in (0,2,4))},0.2);color:{badge_color};padding:3px 10px;border-radius:10px;font-size:0.75rem;font-weight:600;border:1px solid {badge_color}33;">{level}</span>',
                        unsafe_allow_html=True,
                    )
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:3rem;">
            <span style="font-size:3rem;">📤</span>
            <p style="color:#94a3b8;font-size:1.1rem;margin-top:1rem;">Upload your resume to see your parsed profile here</p>
            <p style="color:#64748b;">Go to the Upload tab to get started</p>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════
# TAB: Open Jobs
# ═══════════════════════════════════════════
with tab_jobs:
    st.subheader("💼 Open Positions")
    st.caption("Browse available positions and check if your skills match")

    jobs = api_get("/jobs/", params={"status": "active"})

    if jobs:
        st.markdown(f"**{len(jobs)} position(s) currently open**")
        for job in jobs:
            with st.expander(f"💼 {job['title']}", expanded=False):
                st.markdown(f"**Description:** {job.get('description', '')[:500]}...")

                req_skills = job.get("required_skills") or []
                pref_skills = job.get("preferred_skills") or []

                if req_skills:
                    st.markdown("**Required Skills:**")
                    req_html = " ".join(
                        f'<span style="display:inline-block;background:rgba(239,68,68,0.1);color:#f87171;padding:4px 12px;border-radius:16px;margin:3px;font-size:0.8rem;border:1px solid rgba(239,68,68,0.3);">{s}</span>'
                        for s in req_skills
                    )
                    st.markdown(req_html, unsafe_allow_html=True)

                if pref_skills:
                    st.markdown("**Preferred Skills:**")
                    pref_html = " ".join(
                        f'<span style="display:inline-block;background:rgba(34,197,94,0.1);color:#4ade80;padding:4px 12px;border-radius:16px;margin:3px;font-size:0.8rem;border:1px solid rgba(34,197,94,0.3);">{s}</span>'
                        for s in pref_skills
                    )
                    st.markdown(pref_html, unsafe_allow_html=True)

                if job.get("experience_level"):
                    st.markdown(f"**Experience Level:** {job['experience_level'].title()}")
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:3rem;">
            <span style="font-size:3rem;">💼</span>
            <p style="color:#94a3b8;font-size:1.1rem;margin-top:1rem;">No open positions at the moment</p>
            <p style="color:#64748b;">Check back later for new opportunities!</p>
        </div>
        """, unsafe_allow_html=True)
