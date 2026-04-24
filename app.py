"""
app.py – StyleAI Streamlit frontend.

4 Tabs:
  1. 👗 Inputs       → Event, Personal & Preferences forms
  2. ✨ Outfit        → Agentic run + reasoning chain + final recommendation
  3. 🖼️ Inspiration   → Outfit image gallery pulled from tools
  4. 📋 Logs          → Saved session logs viewer
"""

import json
import time
import datetime
import streamlit as st

try:
    from streamlit_lottie import st_lottie as streamlit_lottie  # optional enhancement
    _HAS_LOTTIE = True
except ImportError:
    _HAS_LOTTIE = False

# ── Page config must be first ─────────────────────────────────────────────────
st.set_page_config(
    page_title="StyleAI – Your AI Fashion Stylist",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports after page config ─────────────────────────────────────────────────
from code.agent  import run_agent
from code.tools  import get_outfit_images, TOOL_REGISTRY
from code.logger import save_session_log, list_log_files, load_log_file
from prompts.stylist_prompt import USER_QUERY_TEMPLATE

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS – vibrant gradient theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── Root variables ── */
:root {
  --grad1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --grad2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --grad3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --grad4: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  --grad5: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  --card-bg: rgba(255,255,255,0.07);
  --border: rgba(255,255,255,0.15);
}

/* ── Global background ── */
.stApp {
  background: linear-gradient(160deg, #0f0c29, #302b63, #24243e);
  color: #f0f0f0;
  font-family: 'Inter', sans-serif;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-right: 1px solid var(--border);
}

/* ── Headings ── */
h1, h2, h3 { font-family: 'Playfair Display', serif; }

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 4px;
  gap: 4px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px;
  padding: 10px 24px;
  font-weight: 600;
  color: rgba(255,255,255,0.6);
  transition: all 0.3s ease;
}
.stTabs [aria-selected="true"] {
  background: var(--grad1) !important;
  color: white !important;
}

/* ── Cards ── */
.style-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
}

/* ── Gradient badges ── */
.badge-purple  { background: var(--grad1); }
.badge-pink    { background: var(--grad2); }
.badge-blue    { background: var(--grad3); }
.badge-green   { background: var(--grad4); }
.badge-sunset  { background: var(--grad5); }
.badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  margin: 3px;
}

/* ── Step cards in reasoning chain ── */
.step-thinking {
  background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));
  border-left: 4px solid #667eea;
  border-radius: 0 12px 12px 0;
  padding: 12px 16px;
  margin: 8px 0;
}
.step-tool-call {
  background: linear-gradient(135deg, rgba(240,147,251,0.2), rgba(245,87,108,0.2));
  border-left: 4px solid #f093fb;
  border-radius: 0 12px 12px 0;
  padding: 12px 16px;
  margin: 8px 0;
}
.step-tool-result {
  background: linear-gradient(135deg, rgba(79,172,254,0.2), rgba(0,242,254,0.2));
  border-left: 4px solid #4facfe;
  border-radius: 0 12px 12px 0;
  padding: 12px 16px;
  margin: 8px 0;
}
.step-final {
  background: linear-gradient(135deg, rgba(67,233,123,0.2), rgba(56,249,215,0.2));
  border-left: 4px solid #43e97b;
  border-radius: 0 12px 12px 0;
  padding: 16px 20px;
  margin: 12px 0;
}
.step-error {
  background: linear-gradient(135deg, rgba(255,77,77,0.2), rgba(255,153,0,0.2));
  border-left: 4px solid #ff4d4d;
  border-radius: 0 12px 12px 0;
  padding: 12px 16px;
  margin: 8px 0;
}

/* ── Input sections ── */
.section-header {
  font-family: 'Playfair Display', serif;
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 12px;
  background: var(--grad1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ── Buttons ── */
.stButton > button {
  background: var(--grad1) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 12px 32px !important;
  font-weight: 700 !important;
  font-size: 1.05rem !important;
  transition: transform 0.2s, box-shadow 0.2s !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(102,126,234,0.5) !important;
}

/* ── Image cards ── */
.img-card {
  border-radius: 16px;
  overflow: hidden;
  border: 2px solid var(--border);
  transition: transform 0.3s, box-shadow 0.3s;
}
.img-card:hover {
  transform: scale(1.03);
  box-shadow: 0 12px 40px rgba(102,126,234,0.4);
}

/* ── Colour swatch ── */
.color-swatch {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: inline-block;
  margin: 4px;
  border: 2px solid rgba(255,255,255,0.3);
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }

/* ── Form labels – bright & readable ── */
label,
.stTextInput > label,
.stSelectbox > label,
.stMultiSelect > label,
.stRadio > label,
.stSlider > label,
.stDateInput > label,
.stTextArea > label,
.stNumberInput > label,
[data-testid="stWidgetLabel"] {
  color: rgba(255, 255, 255, 0.92) !important;
  font-weight: 500 !important;
  letter-spacing: 0.02em !important;
}
/* Multiselect tag text */
.stMultiSelect [data-baseweb="tag"] span { color: #fff !important; }
/* Selectbox / radio option text */
.stRadio [data-testid="stMarkdownContainer"] p { color: rgba(255,255,255,0.88) !important; }
/* Slider tick labels */
.stSlider [data-testid="stTickBar"] * { color: rgba(255,255,255,0.65) !important; }
/* Select slider value */
.stSelectSlider [data-testid="stTickBarMin"],
.stSelectSlider [data-testid="stTickBarMax"] { color: rgba(255,255,255,0.65) !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "agent_steps":       [],
        "final_answer":      "",
        "outfit_images":     [],
        "pinterest_items":   [],
        "image_query":       "",
        "inputs_submitted":  False,
        "running":           False,
        "form_data":         {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px;">
      <div style="font-size:4rem;">👗</div>
      <h1 style="font-family:'Playfair Display',serif; font-size:1.8rem;
                 background:linear-gradient(135deg,#f093fb,#f5576c);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                 margin:0;">StyleAI</h1>
      <p style="color:rgba(255,255,255,0.5); font-size:0.85rem; margin-top:4px;">
        Your Agentic Fashion Stylist
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Fashion visual – animated image spotlight ────────────────────────────
    st.markdown("### ✨ Style of the Moment")
    st.markdown("""
    <style>
    /* 8 images, each visible for ~3s → total cycle = 24s */
    @keyframes fashionFade {
      0%        { opacity:1; transform:scale(1);    }
      10%       { opacity:1; transform:scale(1.04); }
      12.5%     { opacity:0; transform:scale(1.04); }
      12.51%    { opacity:0; transform:scale(1);    }
      100%      { opacity:0; transform:scale(1);    }
    }
    .fashion-frame {
      position:relative; width:100%; padding-bottom:140%;
      border-radius:16px; overflow:hidden;
      border:2px solid rgba(255,255,255,0.15);
      box-shadow: 0 8px 32px rgba(102,126,234,0.4);
    }
    .fashion-frame img {
      position:absolute; top:0; left:0;
      width:100%; height:100%; object-fit:cover;
      border-radius:14px; opacity:0;
      animation: fashionFade 24s ease-in-out infinite;
    }
    /* stagger each image by 3s (24s / 8 images) */
    .fashion-frame img:nth-child(1) { animation-delay:  0s;  opacity:1; }
    .fashion-frame img:nth-child(2) { animation-delay:  3s;  }
    .fashion-frame img:nth-child(3) { animation-delay:  6s;  }
    .fashion-frame img:nth-child(4) { animation-delay:  9s;  }
    .fashion-frame img:nth-child(5) { animation-delay: 12s;  }
    .fashion-frame img:nth-child(6) { animation-delay: 15s;  }
    .fashion-frame img:nth-child(7) { animation-delay: 18s;  }
    .fashion-frame img:nth-child(8) { animation-delay: 21s;  }

    /* slide-in label at bottom */
    .fashion-caption {
      position:absolute; bottom:0; left:0; right:0;
      background:linear-gradient(transparent, rgba(0,0,0,0.7));
      padding:24px 10px 8px;
      border-radius:0 0 14px 14px;
      text-align:center;
    }
    .fashion-caption span {
      font-size:0.65rem; color:rgba(255,255,255,0.55);
      font-family:'Inter',sans-serif; letter-spacing:1px;
    }
    </style>
    <div class="fashion-frame">
      <img src="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&q=80" alt="editorial 1">
      <img src="https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&q=80" alt="editorial 2">
      <img src="https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&q=80" alt="editorial 3">
      <img src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&q=80" alt="editorial 4">
      <img src="https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&q=80" alt="editorial 5">
      <img src="https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&q=80" alt="editorial 6">
      <img src="https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&q=80" alt="editorial 7">
      <img src="https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400&q=80" alt="editorial 8">
      <div class="fashion-caption"><span>✦ FASHION EDITORIALS ✦</span></div>
    </div>
    <p style="color:rgba(255,255,255,0.35); font-size:0.68rem; text-align:center; margin-top:6px;">
      📸 Unsplash · 8 curated looks
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Tool status ───────────────────────────────────────────────────────────
    st.markdown("### 🛠️ Available Tools")
    for name, meta in TOOL_REGISTRY.items():
        st.markdown(
            f'<span class="badge badge-purple">{meta["emoji"]} {name}</span>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── API key quick-check ───────────────────────────────────────────────────
    st.markdown("### ⚙️ API Status")
    from code.config import GEMINI_API_KEY, OPENWEATHER_API_KEY, NEWS_API_KEY

    def _status(key, label):
        ok = bool(key)
        colour = "#43e97b" if ok else "#f5576c"
        icon   = "✅" if ok else "❌"
        st.markdown(
            f'<p style="color:{colour}; font-size:0.85rem; margin:2px 0;">'
            f'{icon} {label}</p>',
            unsafe_allow_html=True
        )

    _status(GEMINI_API_KEY,       "Gemini AI")
    _status(OPENWEATHER_API_KEY,  "OpenWeather")
    _status(NEWS_API_KEY,         "NewsAPI")

    st.markdown("---")
    st.markdown(
        '<p style="color:rgba(255,255,255,0.3); font-size:0.75rem; text-align:center;">'
        'StyleAI v1.0 · EAG Assignment 3</p>',
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hero header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 30px 0 10px;">
  <h1 style="font-family:'Playfair Display',serif; font-size:3rem;
             background:linear-gradient(135deg,#f093fb 0%,#f5576c 40%,#4facfe 100%);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
    ✨ StyleAI – Agentic Fashion Stylist
  </h1>
  <p style="color:rgba(255,255,255,0.6); font-size:1.1rem; max-width:600px; margin:0 auto;">
    Tell me about your event, yourself, and your style — I'll research the weather,
    latest trends, and dress codes to build your perfect outfit.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4 Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "👗 Inputs",
    "✨ Outfit Recommendation",
    "🖼️ Style Inspiration",
    "📋 Session Logs",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – INPUTS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="style-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-header">🎪 Event Details</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        event_type      = st.selectbox("Event Type", [
            "Wedding", "Cocktail Party", "Business Meeting",
            "Casual Outing", "Date Night", "Festival",
            "Beach / Pool", "Gym / Workout", "Other"
        ])
        event_date      = st.date_input("Event Date", value=datetime.date.today())
        indoor_outdoor  = st.radio("Setting", ["Indoor", "Outdoor", "Both"], horizontal=True)
    with col2:
        event_city      = st.text_input("City",         placeholder="e.g. Mumbai")
        event_area      = st.text_input("Area / Venue", placeholder="e.g. Bandra Kurla Complex")
        event_notes     = st.text_area("Extra Notes",   placeholder="e.g. evening garden party, semi-formal…", height=100)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Personal Details ──────────────────────────────────────────────────────
    st.markdown('<div class="style-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-header">🙋 Personal Details</p>', unsafe_allow_html=True)

    col3, col4, col5 = st.columns(3)
    with col3:
        gender    = st.selectbox("Gender", ["Female", "Male", "Non-binary / Other"])
        body_type = st.selectbox("Body Type", [
            "Petite", "Athletic", "Curvy", "Straight / Rectangle",
            "Pear / Triangle", "Hourglass", "Apple / Oval"
        ])
    with col4:
        age       = st.slider("Age", 16, 80, 28)
        skin_tone = st.selectbox("Skin Tone", ["Fair", "Medium", "Olive", "Dark", "Neutral"])
    with col5:
        height    = st.text_input("Height", placeholder="e.g. 5'5\" or 165 cm")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Preferences ───────────────────────────────────────────────────────────
    st.markdown('<div class="style-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-header">💜 Style Preferences</p>', unsafe_allow_html=True)

    col6, col7 = st.columns(2)
    with col6:
        fav_styles = st.multiselect("Favourite Styles", [
            "Boho", "Classic / Preppy", "Streetwear", "Minimalist",
            "Maximalist / Bold", "Romantic / Feminine", "Edgy / Rock",
            "Athleisure", "Vintage / Retro", "Business Chic"
        ])
        fav_colors = st.multiselect("Favourite Colours", [
            "Black", "White", "Navy", "Beige / Nude", "Pastel",
            "Earth Tones", "Jewel Tones", "Bright / Neon", "Prints / Patterns"
        ])
        budget = st.select_slider(
            "Budget Range",
            options=["₹500–1,500", "₹1,500–5,000", "₹5,000–15,000",
                     "₹15,000–50,000", "₹50,000+"],
            value="₹5,000–15,000"
        )
    with col7:
        comfort_priority = st.slider("Comfort Priority (1 = fashion-first, 10 = comfort-first)", 1, 10, 6)
        brands = st.text_input("Brands / Labels you love", placeholder="e.g. Zara, Mango, Sabyasachi")
        avoid  = st.text_area("Anything to avoid?",
                              placeholder="e.g. very short hemlines, synthetic fabrics, stilettos",
                              height=80)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Submit ────────────────────────────────────────────────────────────────
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        submit = st.button("🚀 Get My Outfit Recommendation", use_container_width=True)

    if submit:
        # Store form data
        st.session_state["form_data"] = {
            "event_type":     event_type,
            "event_date":     str(event_date),
            "event_city":     event_city or "Mumbai",
            "event_area":     event_area or "",
            "indoor_outdoor": indoor_outdoor,
            "event_notes":    event_notes or "None",
            "gender":         gender,
            "age":            str(age),
            "body_type":      body_type,
            "skin_tone":      skin_tone.lower(),
            "height":         height or "Not specified",
            "fav_styles":     ", ".join(fav_styles) if fav_styles else "No preference",
            "fav_colors":     ", ".join(fav_colors) if fav_colors else "No preference",
            "budget":         budget,
            "comfort_priority": str(comfort_priority),
            "brands":         brands or "None",
            "avoid":          avoid or "None",
        }
        st.session_state["agent_steps"]      = []
        st.session_state["final_answer"]     = ""
        st.session_state["outfit_images"]    = []
        st.session_state["inputs_submitted"] = True
        st.success("✅ Inputs saved! Head to the **✨ Outfit Recommendation** tab to see the magic.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – OUTFIT RECOMMENDATION
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state["inputs_submitted"]:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px;">
          <div style="font-size:5rem;">👗</div>
          <h2 style="font-family:'Playfair Display',serif; color:rgba(255,255,255,0.7);">
            Fill in your details first!
          </h2>
          <p style="color:rgba(255,255,255,0.4);">
            Go to the <strong>👗 Inputs</strong> tab, fill in the form and hit
            <em>Get My Outfit Recommendation</em>.
          </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        fd = st.session_state["form_data"]

        # ── Show a summary banner ─────────────────────────────────────────────
        st.markdown(f"""
        <div class="style-card" style="background:linear-gradient(135deg,rgba(102,126,234,0.3),rgba(118,75,162,0.3));">
          <h3 style="margin:0 0 8px;">🎯 Your Style Profile</h3>
          <div>
            <span class="badge badge-purple">📅 {fd['event_date']}</span>
            <span class="badge badge-pink">📍 {fd['event_city']}</span>
            <span class="badge badge-blue">🎪 {fd['event_type']}</span>
            <span class="badge badge-green">👤 {fd['gender']}, {fd['age']} yrs</span>
            <span class="badge badge-sunset">💰 {fd['budget']}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Run agent button ──────────────────────────────────────────────────
        col_run, _ = st.columns([1, 3])
        with col_run:
            run_btn = st.button("🤖 Run AI Stylist Agent", use_container_width=True)

        if run_btn and not st.session_state["running"]:
            st.session_state["running"]      = True
            st.session_state["agent_steps"]  = []
            st.session_state["final_answer"] = ""

            user_query = USER_QUERY_TEMPLATE.format(**fd)

            # ── Reasoning chain display area ──────────────────────────────────
            chain_container = st.container()
            with chain_container:
                st.markdown("### 🧠 Agent Reasoning Chain")

                step_placeholder = st.empty()
                steps_html = ""

                for step in run_agent(user_query):
                    st.session_state["agent_steps"].append(step)

                    if step["type"] == "thinking":
                        snippet = step["content"][:400].replace("\n", "<br>") + ("…" if len(step["content"]) > 400 else "")
                        steps_html += f"""
                        <div class="step-thinking">
                          <strong>🧠 Step {step['step']} – Thinking</strong><br>
                          <span style="font-size:0.85rem; color:rgba(255,255,255,0.75);">{snippet}</span>
                        </div>"""

                    elif step["type"] == "tool_call":
                        emoji = TOOL_REGISTRY.get(step["tool_name"], {}).get("emoji", "🔧")
                        steps_html += f"""
                        <div class="step-tool-call">
                          <strong>{emoji} Step {step['step']} – Tool Call: <code>{step['tool_name']}</code></strong><br>
                          <span style="font-size:0.83rem; color:rgba(255,255,255,0.65);">
                            Args: {json.dumps(step['tool_args'])}
                          </span>
                        </div>"""

                    elif step["type"] == "tool_result":
                        try:
                            result_obj = json.loads(step["content"])
                            result_str = json.dumps(result_obj, indent=2)[:600]
                        except Exception:
                            result_str = step["content"][:600]
                        steps_html += f"""
                        <div class="step-tool-result">
                          <strong>📊 Step {step['step']} – Tool Result: <code>{step['tool_name']}</code></strong><br>
                          <pre style="font-size:0.75rem; color:rgba(255,255,255,0.65);
                                      white-space:pre-wrap; margin:4px 0 0;">{result_str}</pre>
                        </div>"""

                    elif step["type"] == "final":
                        st.session_state["final_answer"] = step["content"]

                    elif step["type"] == "error":
                        steps_html += f"""
                        <div class="step-error">
                          <strong>❌ Error</strong><br>
                          <span style="font-size:0.85rem;">{step['content']}</span>
                        </div>"""

                    step_placeholder.markdown(steps_html, unsafe_allow_html=True)

            # ── Final recommendation ──────────────────────────────────────────
            if st.session_state["final_answer"]:
                st.markdown("---")
                st.markdown("""
                <div style="text-align:center; margin-bottom:16px;">
                  <h2 style="font-family:'Playfair Display',serif;
                             background:linear-gradient(135deg,#43e97b,#38f9d7);
                             -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    ✨ Your Perfect Outfit
                  </h2>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f'<div class="step-final">{st.session_state["final_answer"]}</div>',
                    unsafe_allow_html=True
                )

                # Auto-fetch outfit images
                image_query = f"{fd['event_type']} outfit {fd.get('fav_styles','fashion')}"
                img_result  = get_outfit_images(image_query, count=6)
                st.session_state["outfit_images"] = img_result.get("images", [])
                st.session_state["image_query"]   = image_query

                # Save log
                session_log = {
                    "timestamp":  datetime.datetime.now().isoformat(),
                    "form_data":  fd,
                    "agent_steps": [
                        {k: v for k, v in s.items() if k != "content"}
                        | {"content_preview": str(s.get("content", ""))[:300]}
                        for s in st.session_state["agent_steps"]
                    ],
                    "final_answer": st.session_state["final_answer"],
                }
                log_path = save_session_log(session_log)
                st.success(f"💾 Session saved → `{log_path}`")

            st.session_state["running"] = False

        elif st.session_state["final_answer"]:
            # Previously ran – show cached result
            st.markdown("### 🧠 Agent Reasoning Chain")
            for step in st.session_state["agent_steps"]:
                if step["type"] == "thinking":
                    with st.expander(f"🧠 Step {step['step']} – Thinking", expanded=False):
                        st.write(step["content"])
                elif step["type"] == "tool_call":
                    with st.expander(f"🔧 Step {step['step']} – Tool: {step['tool_name']}", expanded=False):
                        st.json(step.get("tool_args", {}))
                elif step["type"] == "tool_result":
                    with st.expander(f"📊 Step {step['step']} – Result: {step['tool_name']}", expanded=False):
                        try:
                            st.json(json.loads(step["content"]))
                        except Exception:
                            st.write(step["content"])

            st.markdown("---")
            st.markdown('<div class="step-final">', unsafe_allow_html=True)
            st.markdown(st.session_state["final_answer"])
            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – STYLE INSPIRATION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div style="text-align:center; padding:16px 0 24px;">
      <h2 style="font-family:'Playfair Display',serif;
                 background:linear-gradient(135deg,#f093fb,#4facfe);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        � Pinterest Style Board
      </h2>
      <p style="color:rgba(255,255,255,0.5);">
        Powered by Pexels · Auto-generated from your AI recommendation
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Pinterest masonry CSS ─────────────────────────────────────────────────
    st.markdown("""
    <style>
    .pin-board { column-count:3; column-gap:12px; }
    .pin-item  {
      break-inside:avoid; margin-bottom:12px;
      border-radius:14px; overflow:hidden; position:relative;
      border:1.5px solid rgba(255,255,255,0.12);
      transition:transform 0.3s, box-shadow 0.3s;
    }
    .pin-item:hover {
      transform:scale(1.025);
      box-shadow:0 14px 40px rgba(102,126,234,0.45);
    }
    .pin-item img { width:100%; display:block; border-radius:14px; }
    .pin-overlay {
      position:absolute; bottom:0; left:0; right:0;
      background:linear-gradient(transparent, rgba(0,0,0,0.75));
      padding:28px 10px 10px; border-radius:0 0 14px 14px;
      opacity:0; transition:opacity 0.3s;
    }
    .pin-item:hover .pin-overlay { opacity:1; }
    .pin-label {
      color:white; font-size:0.72rem; font-weight:600;
      margin:0; line-height:1.3;
    }
    .pin-credit {
      color:rgba(255,255,255,0.65); font-size:0.62rem; margin:2px 0 0;
    }
    .pin-section-title {
      font-family:'Playfair Display',serif; font-size:0.85rem; font-weight:700;
      color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:2px;
      margin:20px 0 8px; padding-left:2px;
    }
    @media(max-width:768px){ .pin-board{ column-count:2; } }
    </style>
    """, unsafe_allow_html=True)

    from code.tools import get_color_palette, extract_outfit_queries

    # ── Section A: Auto Pinterest Board from Gemini output ───────────────────
    has_final = bool(st.session_state.get("final_answer"))

    if has_final:
        col_pin, _ = st.columns([1, 3])
        with col_pin:
            pin_btn = st.button("📌 Generate Pinterest Board from Recommendation",
                                use_container_width=True)

        if pin_btn or st.session_state.get("pinterest_items"):
            if pin_btn:
                final_txt = st.session_state["final_answer"]
                queries   = extract_outfit_queries(final_txt, max_items=6)
                st.session_state["pinterest_items"] = queries

            queries = st.session_state.get("pinterest_items", [])

            if queries:
                st.markdown(f"""
                <div class="style-card" style="margin-bottom:12px;">
                  <strong style="color:rgba(255,255,255,0.9);">🔍 Searching for {len(queries)} outfit pieces…</strong><br>
                  <span style="font-size:0.8rem; color:rgba(255,255,255,0.5);">
                    {' &nbsp;·&nbsp; '.join(f'<em>{q[:40]}</em>' for q in queries)}
                  </span>
                </div>
                """, unsafe_allow_html=True)

                all_pins = []
                for q in queries:
                    res = get_outfit_images(q, count=2)
                    imgs = res.get("images", [])
                    for img in imgs:
                        img["section"] = q
                    all_pins.extend(imgs)

                if all_pins:
                    pin_html = '<div class="pin-board">'
                    for img in all_pins:
                        label  = img.get("alt", img.get("section",""))[:55]
                        credit = img.get("photographer", "Pexels")
                        pin_html += f"""
                        <div class="pin-item">
                          <img src="{img['thumb_url']}" alt="{label}" loading="lazy">
                          <div class="pin-overlay">
                            <p class="pin-label">{label}</p>
                            <p class="pin-credit">📸 {credit}</p>
                          </div>
                        </div>"""
                    pin_html += "</div>"
                    st.markdown(pin_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:30px 0; color:rgba(255,255,255,0.4);">
          <div style="font-size:3.5rem;">📌</div>
          <p>Run the AI Stylist first — the board auto-generates from your recommendation.</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Section B: Free search ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="pin-section-title">🔎 Explore Any Style</p>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        img_search = st.text_input(
            "Search outfits",
            value=st.session_state.get("image_query", "fashion outfit"),
            placeholder="e.g. boho wedding guest outfit",
            label_visibility="collapsed",
        )
    with col_s2:
        search_btn = st.button("🔍 Search Pexels", use_container_width=True)

    if search_btn:
        result = get_outfit_images(img_search, count=9)
        images = result.get("images", [])
        st.session_state["outfit_images"] = images
        st.session_state["image_query"]   = img_search

    search_images = st.session_state.get("outfit_images", [])
    if search_images:
        pin_html = '<div class="pin-board">'
        for img in search_images:
            label  = img.get("alt", img_search)[:55]
            credit = img.get("photographer", "Pexels")
            pin_html += f"""
            <div class="pin-item">
              <img src="{img['thumb_url']}" alt="{label}" loading="lazy">
              <div class="pin-overlay">
                <p class="pin-label">{label}</p>
                <p class="pin-credit">📸 {credit}</p>
              </div>
            </div>"""
        pin_html += "</div>"
        st.markdown(pin_html, unsafe_allow_html=True)

    # ── Section C: Colour palette ─────────────────────────────────────────────
    if st.session_state["inputs_submitted"]:
        st.markdown("---")
        st.markdown("""
        <h3 style="font-family:'Playfair Display',serif;
                   background:linear-gradient(135deg,#43e97b,#fee140);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
          🎨 Your Seasonal Colour Palette
        </h3>
        """, unsafe_allow_html=True)

        fd = st.session_state["form_data"]
        palette = get_color_palette(fd["event_date"], fd["skin_tone"])

        p1, p2 = st.columns([2, 3])
        with p1:
            st.markdown(f"**Season:** {palette.get('season','')}")
            st.markdown(f"**Skin-tone tip:** {palette.get('skin_tone_tip','')}")
            st.markdown(f"**Description:** {palette.get('description','')}")
            st.markdown("**Avoid:** " + ", ".join(palette.get("avoid", [])))
        with p2:
            swatch_html = ""
            for colour, hex_code in zip(palette.get("colors",[]), palette.get("hex",[])):
                swatch_html += (
                    f'<span class="color-swatch" style="background:{hex_code};" '
                    f'title="{colour} ({hex_code})"></span>'
                )
            st.markdown(swatch_html, unsafe_allow_html=True)
            for colour, hex_code in zip(palette.get("colors",[]), palette.get("hex",[])):
                light = hex_code in ["#FFFFFF","#FFFACD","#FFF44F","#FFFFF0","#FFDB58"]
                st.markdown(
                    f'<span class="badge" style="background:{hex_code}; color:{"#000" if light else "#fff"};">'
                    f'{colour}</span>',
                    unsafe_allow_html=True
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – SESSION LOGS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <h2 style="font-family:'Playfair Display',serif;
               background:linear-gradient(135deg,#fa709a,#fee140);
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
      📋 Session Logs
    </h2>
    <p style="color:rgba(255,255,255,0.5); margin-bottom:20px;">
      Every agent run is saved here for review and replay.
    </p>
    """, unsafe_allow_html=True)

    log_files = list_log_files()

    if not log_files:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:rgba(255,255,255,0.4);">
          <div style="font-size:3rem;">📂</div>
          <p>No session logs yet. Run the agent first!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        selected_log = st.selectbox(
            "Select a session log",
            log_files,
            format_func=lambda p: p.split("\\")[-1].split("/")[-1]
        )

        if selected_log:
            log_data = load_log_file(selected_log)

            # ── Summary header ────────────────────────────────────────────────
            fd_log = log_data.get("form_data", {})
            st.markdown(f"""
            <div class="style-card">
              <strong>🎪 {fd_log.get('event_type','?')}</strong> &nbsp;| &nbsp;
              <strong>📍 {fd_log.get('event_city','?')}</strong> &nbsp;| &nbsp;
              <strong>📅 {fd_log.get('event_date','?')}</strong><br>
              <small style="color:rgba(255,255,255,0.4);">Logged: {log_data.get('timestamp','')}</small>
            </div>
            """, unsafe_allow_html=True)

            # ── Steps ─────────────────────────────────────────────────────────
            st.markdown("#### 🧠 Agent Steps")
            for step in log_data.get("agent_steps", []):
                label = f"Step {step.get('step','?')} – {step.get('type','').title()}"
                with st.expander(label, expanded=False):
                    st.write(step.get("content_preview", ""))
                    if step.get("tool_name"):
                        st.write(f"**Tool:** `{step['tool_name']}`")

            # ── Final answer ──────────────────────────────────────────────────
            st.markdown("#### ✨ Final Recommendation")
            st.markdown(
                f'<div class="step-final">{log_data.get("final_answer","No answer saved.")}</div>',
                unsafe_allow_html=True
            )

            # ── Raw JSON ──────────────────────────────────────────────────────
            with st.expander("📄 Raw JSON Log", expanded=False):
                st.json(log_data)
