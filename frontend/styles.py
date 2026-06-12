"""
AI Resume Analyzer — Shared Streamlit Styles

Provides consistent CSS theming with background image, glassmorphism,
animations, and premium design across all pages.
"""

import base64
from pathlib import Path


def _get_bg_image_base64() -> str:
    """Load and cache the background image as base64."""
    img_path = Path(__file__).parent / "ai_background.png"
    if img_path.exists():
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


# Cache the image data at module load
_BG_IMAGE_B64 = _get_bg_image_base64()


def get_global_css() -> str:
    """
    Return the full global CSS string for Streamlit injection.
    Includes background image, glassmorphism, animations, and typography.
    """
    bg_url = f"data:image/png;base64,{_BG_IMAGE_B64}" if _BG_IMAGE_B64 else ""

    bg_css = ""
    if bg_url:
        bg_css = f"""
        /* ── Background image with low opacity ── */
        .stApp {{
            background-color: #0f0b1e;
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
            opacity: 0.12;
            z-index: -1;
            pointer-events: none;
        }}
        """

    return f"""
<style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    {bg_css}

    /* ── Dark theme base ── */
    .stApp {{
        color: #e2e8f0;
    }}

    /* ── Glassmorphism hero header ── */
    .hero-header {{
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.9) 0%, rgba(124, 58, 237, 0.9) 50%, rgba(168, 85, 247, 0.9) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 2.5rem 3rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(79, 70, 229, 0.35), 0 0 80px rgba(124, 58, 237, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }}
    .hero-header::after {{
        content: "";
        position: absolute;
        top: -50%;
        right: -30%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .hero-header h1 {{
        color: white;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }}
    .hero-header p {{
        color: #e0d4ff;
        font-size: 1.05rem;
        margin: 0.5rem 0 0;
        font-weight: 400;
    }}

    /* ── Glassmorphism cards ── */
    .glass-card {{
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .glass-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(79, 70, 229, 0.2);
        border-color: rgba(124, 58, 237, 0.3);
    }}
    .glass-card h3 {{
        color: #c4b5fd;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0 0 0.5rem;
    }}
    .glass-card .value {{
        color: #f1f5f9;
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }}
    .glass-card .desc {{
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        line-height: 1.5;
    }}

    /* ── Metric cards ── */
    .metric-card {{
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .metric-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(79, 70, 229, 0.2);
        border-color: rgba(124, 58, 237, 0.3);
    }}
    .metric-card h3 {{
        color: #c4b5fd;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0;
    }}
    .metric-card p {{
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        margin-top: 0.5rem !important;
        line-height: 1.5 !important;
    }}

    /* ── Status badges ── */
    .badge-success {{
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }}
    .badge-warning {{
        background: rgba(250, 204, 21, 0.15);
        color: #facc15;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(250, 204, 21, 0.3);
    }}
    .badge-danger {{
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .badge-llm {{
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.2), rgba(168, 85, 247, 0.2));
        color: #c4b5fd;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(124, 58, 237, 0.4);
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}

    /* ── Sidebar styling ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0f0b1e 0%, #1a1145 50%, #1e1b4b 100%) !important;
        border-right: 1px solid rgba(124, 58, 237, 0.2);
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
        color: #e2e8f0;
    }}

    /* ── Button styling ── */
    .stButton > button {{
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.3);
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        border: none;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    }}

    /* ── Form inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
    }}
    .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: rgba(255, 255, 255, 0.03);
        padding: 4px;
        border-radius: 12px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        color: #94a3b8;
    }}
    .stTabs [aria-selected="true"] {{
        background: rgba(79, 70, 229, 0.2) !important;
        color: #c4b5fd !important;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
    }}
    .streamlit-expanderContent {{
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 0 0 12px 12px !important;
    }}

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {{
        color: #f1f5f9 !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: #94a3b8 !important;
    }}

    /* ── Getting started guide ── */
    .getting-started {{
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2rem;
        margin-top: 1.5rem;
    }}
    .getting-started h3 {{
        color: #c4b5fd;
        margin-top: 0;
    }}
    .step-item {{
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 16px;
        margin: 10px 0;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.2s;
    }}
    .step-item:hover {{
        background: rgba(79, 70, 229, 0.08);
        border-color: rgba(124, 58, 237, 0.2);
    }}
    .step-num {{
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        flex-shrink: 0;
    }}
    .step-content {{
        flex: 1;
    }}
    .step-content strong {{
        color: #e2e8f0;
        font-size: 0.95rem;
    }}
    .step-content p {{
        color: #94a3b8;
        font-size: 0.85rem;
        margin: 4px 0 0;
    }}

    /* ── LLM status indicator ── */
    .llm-status {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    .llm-status.active {{
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #4ade80;
    }}
    .llm-status.inactive {{
        background: rgba(250, 204, 21, 0.1);
        border: 1px solid rgba(250, 204, 21, 0.3);
        color: #facc15;
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
    @keyframes pulse-glow {{
        0%, 100% {{ box-shadow: 0 0 5px rgba(124, 58, 237, 0.2); }}
        50% {{ box-shadow: 0 0 20px rgba(124, 58, 237, 0.4); }}
    }}
    .hero-header {{
        animation: fadeInUp 0.6s ease-out;
    }}
    .glass-card, .metric-card {{
        animation: fadeInUp 0.6s ease-out;
    }}

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {{
        background: rgba(255, 255, 255, 0.03);
        border: 2px dashed rgba(124, 58, 237, 0.3);
        border-radius: 16px;
        padding: 1rem;
        transition: all 0.3s;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: rgba(124, 58, 237, 0.6);
        background: rgba(79, 70, 229, 0.05);
    }}

    /* ── Hide Streamlit branding ── */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* ── Progress bars ── */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, #4f46e5, #7c3aed, #a855f7) !important;
    }}

    /* ── Footer ── */
    .app-footer {{
        text-align: center;
        padding: 2rem 0 1rem;
        color: #475569;
        font-size: 0.8rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 3rem;
    }}
    .app-footer a {{
        color: #7c3aed;
        text-decoration: none;
    }}
</style>
"""
