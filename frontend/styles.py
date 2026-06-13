"""
AI Resume Analyzer — Shared Streamlit Styles

Provides consistent CSS theming with background image, glassmorphism,
animations, and premium design across all pages.
"""

import base64
from pathlib import Path
import streamlit as st


def _get_bg_image_base64() -> str:
    """Load the background image as base64 dynamically, with session state caching."""
    # Try session state first
    if "bg_image_b64" in st.session_state and st.session_state["bg_image_b64"]:
        return st.session_state["bg_image_b64"]

    frontend_dir = Path(__file__).parent
    img_path = frontend_dir / "ai_background.png"

    if img_path.exists():
        try:
            with open(img_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode()
                st.session_state["bg_image_b64"] = b64_data
                return b64_data
        except Exception:
            pass
    return ""


def get_global_css() -> str:
    """
    Return the full global CSS string for Streamlit injection.
    Includes background image, glassmorphism, animations, and typography.
    """
    bg_b64 = _get_bg_image_base64()
    bg_url = f"data:image/png;base64,{bg_b64}" if bg_b64 else ""

    bg_css = ""
    if bg_url:
        bg_css = f"""
        /* ── Background image with overlay ── */
        body {{
            background-color: #0b071a !important;
        }}
        .stApp {{
            background-color: transparent !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("{bg_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            opacity: 0.25;
            z-index: -2;
            pointer-events: none;
            filter: saturate(1.2) brightness(1.05);
        }}
        .stApp::after {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 50% 50%, transparent 20%, rgba(11, 7, 26, 0.75) 100%);
            z-index: -1;
            pointer-events: none;
        }}
        """

    return f"""
<style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    h1, h2, h3, h4, h5, h6, .hero-header h1 {{
        font-family: 'Outfit', sans-serif;
    }}

    {bg_css}

    /* ── Dark theme base ── */
    .stApp {{
        color: #f1f5f9;
    }}

    /* ── Glassmorphism hero header ── */
    .hero-header {{
        background: linear-gradient(135deg, rgba(30, 20, 80, 0.6) 0%, rgba(15, 11, 30, 0.85) 100%);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        padding: 2.5rem 3rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(124, 58, 237, 0.25), inset 0 1px 1px rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(124, 58, 237, 0.25);
        position: relative;
        overflow: hidden;
        transition: border-color 0.5s ease, box-shadow 0.5s ease;
    }}
    .hero-header:hover {{
        border-color: rgba(168, 85, 247, 0.45);
        box-shadow: 0 15px 45px rgba(168, 85, 247, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.25);
    }}
    .hero-header::after {{
        content: "";
        position: absolute;
        top: -50%;
        right: -30%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(168, 85, 247, 0.12) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .hero-header h1 {{
        color: white;
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }}
    .hero-header p {{
        color: #e9d5ff;
        font-size: 1.1rem;
        margin: 0.6rem 0 0;
        font-weight: 400;
    }}

    /* ── Glassmorphism cards ── */
    .glass-card, .metric-card {{
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 1.8rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }}
    .glass-card::before, .metric-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 20px;
        padding: 1px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(124, 58, 237, 0.05) 50%, rgba(255, 255, 255, 0.02) 100%);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
    }}
    .glass-card:hover, .metric-card:hover {{
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.05);
        box-shadow: 0 15px 35px rgba(124, 58, 237, 0.15), 0 0 1px rgba(255, 255, 255, 0.2);
        border-color: rgba(124, 58, 237, 0.35);
    }}
    .glass-card h3 {{
        color: #d8b4fe;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0 0 0.5rem;
    }}
    .glass-card .value {{
        color: #f8fafc;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }}
    .glass-card .desc {{
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 0.5rem;
        line-height: 1.6;
    }}

    /* ── Metric cards ── */
    .metric-card {{
        text-align: center;
    }}
    .metric-card h3 {{
        color: #d8b4fe;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0;
    }}
    .metric-card p {{
        color: #cbd5e1 !important;
        font-size: 0.95rem !important;
        margin-top: 0.6rem !important;
        line-height: 1.6 !important;
    }}

    /* ── Status badges ── */
    .badge-success {{
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }}
    .badge-warning {{
        background: rgba(250, 204, 21, 0.15);
        color: #facc15;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(250, 204, 21, 0.3);
    }}
    .badge-danger {{
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .badge-llm {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2));
        color: #e9d5ff;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(168, 85, 247, 0.4);
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}

    /* ── Sidebar styling ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(15, 11, 30, 0.95) 0%, rgba(26, 17, 69, 0.95) 100%) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
        color: #f1f5f9;
    }}

    /* ── Button styling ── */
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background: rgba(255, 255, 255, 0.03) !important;
        color: #f1f5f9 !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        background: rgba(255, 255, 255, 0.06) !important;
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.2) !important;
        border-color: rgba(124, 58, 237, 0.3) !important;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.45) !important;
        transform: translateY(-2px) !important;
    }}

    /* ── Form inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        transition: all 0.3s ease !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: rgba(168, 85, 247, 0.6) !important;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.25) !important;
        background: rgba(255, 255, 255, 0.04) !important;
    }}
    .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px !important;
        background: rgba(255, 255, 255, 0.02) !important;
        padding: 6px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        transition: all 0.3s ease !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.25)) !important;
        color: #e9d5ff !important;
        border: 1px solid rgba(168, 85, 247, 0.35) !important;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        transition: all 0.3s !important;
    }}
    .streamlit-expanderHeader:hover {{
        background: rgba(255, 255, 255, 0.04) !important;
        border-color: rgba(124, 58, 237, 0.2) !important;
    }}
    .streamlit-expanderContent {{
        background: rgba(255, 255, 255, 0.01) !important;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-radius: 0 0 12px 12px !important;
    }}

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {{
        color: #f8fafc !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: #cbd5e1 !important;
        font-size: 0.95rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }}

    /* ── Getting started guide ── */
    .getting-started {{
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 1.5rem;
    }}
    .getting-started h3 {{
        color: #d8b4fe;
        margin-top: 0;
    }}
    .step-item {{
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 16px;
        margin: 12px 0;
        background: rgba(255, 255, 255, 0.01);
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.04);
        transition: all 0.3s ease;
    }}
    .step-item:hover {{
        background: rgba(124, 58, 237, 0.06);
        border-color: rgba(168, 85, 247, 0.2);
        transform: translateX(4px);
    }}
    .step-num {{
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        flex-shrink: 0;
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
    }}
    .step-content {{
        flex: 1;
    }}
    .step-content strong {{
        color: #f1f5f9;
        font-size: 1rem;
    }}
    .step-content p {{
        color: #94a3b8;
        font-size: 0.9rem;
        margin: 4px 0 0;
    }}

    /* ── LLM status indicator ── */
    .llm-status {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.3s;
    }}
    .llm-status.active {{
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #4ade80;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.15);
    }}
    .llm-status.inactive {{
        background: rgba(250, 204, 21, 0.1);
        border: 1px solid rgba(250, 204, 21, 0.3);
        color: #facc15;
        box-shadow: 0 0 15px rgba(250, 204, 21, 0.15);
    }}

    /* ── Animations ── */
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    .hero-header {{
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}
    .glass-card, .metric-card, .getting-started {{
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {{
        background: rgba(255, 255, 255, 0.02) !important;
        border: 2px dashed rgba(168, 85, 247, 0.3) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease !important;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: rgba(168, 85, 247, 0.7) !important;
        background: rgba(124, 58, 237, 0.04) !important;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.15) !important;
    }}

    /* ── Hide Streamlit branding ── */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* ── Progress bars ── */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899) !important;
        border-radius: 10px !important;
        height: 8px !important;
    }}

    /* ── Footer ── */
    .app-footer {{
        text-align: center;
        padding: 2.5rem 0 1.5rem;
        color: #64748b;
        font-size: 0.85rem;
        border-top: 1px solid rgba(255, 255, 255, 0.04);
        margin-top: 4rem;
    }}
    .app-footer a {{
        color: #a855f7;
        text-decoration: none;
        font-weight: 500;
    }}
    .app-footer a:hover {{
        text-decoration: underline;
    }}
</style>
"""



