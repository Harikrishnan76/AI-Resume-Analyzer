"""
AI Resume Analyzer — Streamlit Frontend Entry Point

Main app with authentication (login/register) and navigation.
Premium dark theme with AI background and glassmorphism design.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.utils import login, register, logout, is_logged_in, is_admin, get_user
from frontend.styles import get_global_css

# ── Page Config ──
st.set_page_config(
    page_title="CIT AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Global CSS ──
st.markdown(get_global_css(), unsafe_allow_html=True)


def show_auth_page():
    """Display login/register forms with premium styling."""
    st.markdown("""
    <div class="hero-header" style="text-align:center;">
        <h1>📄 CIT AI Resume Analyzer</h1>
        <p>Smart resume screening powered by AI — upload, analyze, and shortlist in seconds</p>
    </div>
    """, unsafe_allow_html=True)

    # System status indicators
    col_left, col_right = st.columns([3, 1])
    with col_right:
        try:
            from frontend.utils import api_get
            health = api_get("/health")
            if health:
                llm_active = health.get("llm_enabled", False)
                if llm_active:
                    st.markdown('<span class="llm-status active">🤖 LLM Extraction: Active</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="llm-status inactive">⚙️ LLM: Traditional Mode</span>', unsafe_allow_html=True)
        except Exception:
            pass

    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

    with tab_login:
        with st.form("login_form"):
            st.subheader("Welcome Back")
            st.caption("Sign in to access your dashboard")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.warning("⚠️ Please fill in both username and password")
                else:
                    with st.spinner("🔐 Authenticating..."):
                        if login(username, password):
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password. Please try again.")

    with tab_register:
        with st.form("register_form"):
            st.subheader("Create Account")
            st.caption("Join the platform to start analyzing resumes")
            reg_name = st.text_input("Full Name", placeholder="Your full name")
            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
            reg_email = st.text_input("Email", placeholder="your@email.com")
            reg_password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="reg_pass")
            reg_role = st.selectbox(
                "I am a...",
                ["candidate", "admin"],
                format_func=lambda x: "📋 Candidate — Upload resumes & view scores" if x == "candidate" else "👔 Recruiter / Admin — Manage jobs & shortlists",
            )

            submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

            if submitted:
                if not all([reg_name, reg_username, reg_email, reg_password]):
                    st.warning("⚠️ Please fill in all fields to create your account")
                elif len(reg_password) < 6:
                    st.warning("🔒 Password must be at least 6 characters for security")
                elif "@" not in reg_email:
                    st.warning("📧 Please enter a valid email address")
                else:
                    with st.spinner("📝 Creating your account..."):
                        if register(reg_username, reg_email, reg_password, reg_role, reg_name):
                            st.success("✅ Account created successfully! You can now log in.")
                        else:
                            st.error("❌ Registration failed. Username or email may already exist.")


def show_sidebar():
    """Display sidebar with user info and navigation."""
    user = get_user()

    with st.sidebar:
        st.markdown("### 📄 AI Resume Analyzer")
        st.markdown("---")

        # User info
        role_icon = "👔" if is_admin() else "📋"
        role_name = "Admin / Recruiter" if is_admin() else "Candidate"
        st.markdown(f"**{role_icon} {user.get('username', 'User')}**")
        st.caption(f"Role: {role_name}")
        st.markdown("---")

        # Navigation hints
        if is_admin():
            st.markdown("#### 🧭 Quick Navigation")
            st.markdown("""
            - 👔 **Admin Dashboard** — Jobs, scoring, emails
            - 👥 **Candidates** — View all applicants
            - 🎯 **Scoring** — Run AI scoring
            - 📧 **Emails** — Send notifications
            """)
        else:
            st.markdown("#### 🧭 Quick Navigation")
            st.markdown("""
            - 📤 **Upload Resume** — PDF or DOCX
            - 👤 **My Profile** — View extracted data
            - 💼 **Open Jobs** — Browse positions
            """)

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()



        # Footer in sidebar
        st.markdown("---")
        st.caption("v1.0.0 · Powered by AI")


def show_home():
    """Show home page based on role with getting started guide."""
    st.markdown("""
    <div class="hero-header">
        <h1>📄 AI Resume Analyzer</h1>
        <p>Smart resume screening and shortlisting powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

    user = get_user()

    if is_admin():
        st.info("👔 **Welcome, Admin!** — Use the sidebar to navigate to the **Admin Dashboard** to manage jobs, run scoring, and send emails.")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>📋 Job Descriptions</h3>
                <p>Create and manage job postings with required skills and experience levels</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🎯 AI Scoring Engine</h3>
                <p>Run hybrid scoring: keywords + semantic embeddings + rule-based matching</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>📧 Email Automation</h3>
                <p>One-click shortlist/rejection emails with professional templates</p>
            </div>
            """, unsafe_allow_html=True)

        # Getting Started Guide for Admin
        st.markdown("""
        <div class="getting-started">
            <h3>🚀 Getting Started — Admin Guide</h3>
            <div class="step-item">
                <div class="step-num">1</div>
                <div class="step-content">
                    <strong>Create a Job Posting</strong>
                    <p>Go to Admin Dashboard → Jobs tab → Fill in title, description, and required skills</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">2</div>
                <div class="step-content">
                    <strong>Wait for Candidates</strong>
                    <p>Candidates will register and upload their resumes. The AI will automatically extract skills, experience, and education</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">3</div>
                <div class="step-content">
                    <strong>Run AI Scoring</strong>
                    <p>Go to Scoring tab → Select a job → Click "Run Scoring" to rank all candidates</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">4</div>
                <div class="step-content">
                    <strong>Send Notifications</strong>
                    <p>Go to Emails tab → Send shortlist or rejection emails with one click</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("📋 **Welcome, Candidate!** — Use the sidebar to navigate to the **Candidate Portal** to upload your resume and view results.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>📤 Upload Resume</h3>
                <p>Upload your PDF or DOCX resume. Our AI will extract your skills, experience, and education automatically</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🔍 Smart Analysis</h3>
                <p>View your extracted profile with skill tags, experience timeline, and education details</p>
            </div>
            """, unsafe_allow_html=True)

        # Getting Started Guide for Candidate
        st.markdown("""
        <div class="getting-started">
            <h3>🚀 Getting Started — Candidate Guide</h3>
            <div class="step-item">
                <div class="step-num">1</div>
                <div class="step-content">
                    <strong>Upload Your Resume</strong>
                    <p>Go to Candidate Portal → Upload tab → Select your PDF or DOCX resume file</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">2</div>
                <div class="step-content">
                    <strong>Review Your Profile</strong>
                    <p>Check the "My Profile" tab to see extracted skills, experience, and education</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">3</div>
                <div class="step-content">
                    <strong>Browse Open Positions</strong>
                    <p>View available job postings and their required skills to check your fit</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="app-footer">
        <p>AI Resume Analyzer v1.0.0 · Built with ❤️ using FastAPI + Streamlit + OpenAI</p>
    </div>
    """, unsafe_allow_html=True)


if not is_logged_in():
    show_auth_page()
else:
    show_sidebar()
    show_home()
