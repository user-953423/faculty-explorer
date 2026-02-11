import streamlit as st
import pandas as pd
import ast, re
from collections import Counter

# =========================
# Page setup + styling
# =========================
st.set_page_config(page_title="Babson Faculty Research Explorer", layout="wide")

st.markdown("""
<style>
/* ——— Google Fonts: Babson brand-approved web alternates ——— */
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Zilla+Slab:wght@300;400;500;600&display=swap');

/* ——— Babson Brand Color Tokens ——— */
:root {
  --babson-green:       #006644;
  --babson-green-dark:  #004d33;
  --babson-green-light: #e6f2ec;
  --courtyard-green:    #597C31;
  --sherwood-green:     #9EB28F;
  --alfresco:           #567B8A;
  --bright-gold:        #DDD055;
  --mango-punch:        #EEAF00;
  --ocre:               #AD9001;
  --neutral-50:         #fafbfc;
  --neutral-100:        #f1f3f5;
  --neutral-200:        #e4e7eb;
  --neutral-400:        #9ca3af;
  --neutral-600:        #4b5563;
  --neutral-800:        #1f2937;
}

/* ——— Global type ——— */
html, body, [class*="css"] {
  font-family: 'Zilla Slab', Georgia, serif !important;
  color: var(--neutral-800);
}

/* ——— Page container ——— */
.block-container {
  max-width: 1100px;
  padding-top: 0 !important;
  padding-bottom: 2rem;
}

/* ——— Top brand bar ——— */
.brand-bar {
  background: var(--babson-green);
  margin: -1rem -1rem 0 -1rem;
  padding: 1.1rem 1.5rem .9rem;
  border-bottom: 3px solid var(--mango-punch);
}
.brand-bar h1 {
  font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
  font-weight: 600;
  font-size: 1.7rem;
  color: #ffffff;
  margin: 0 !important;
  letter-spacing: .5px;
  text-transform: uppercase;
}
.brand-bar .subtitle {
  font-family: 'Zilla Slab', Georgia, serif;
  color: rgba(255,255,255,.78);
  font-size: .92rem;
  margin: .3rem 0 0 1px;
  font-weight: 300;
}

/* ——— Hide default Streamlit header (we use the brand bar) ——— */
header[data-testid="stHeader"] {
  display: none !important;
}

/* ——— Headings ——— */
h1, h2, h3 {
  font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
  color: var(--babson-green);
}
h2 { font-weight: 600; font-size: 1.35rem; text-transform: uppercase; letter-spacing: .4px; }
h3 { font-weight: 600; font-size: 1.1rem; margin-top: .6rem !important; }

/* ——— Tabs ——— */
button[data-baseweb="tab"] {
  font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
  font-weight: 600 !important;
  font-size: .95rem !important;
  text-transform: uppercase !important;
  letter-spacing: .6px !important;
  color: var(--neutral-600) !important;
  border-bottom: 3px solid transparent !important;
  padding: .6rem 1.2rem !important;
  transition: all .15s ease !important;
}
button[data-baseweb="tab"]:hover {
  color: var(--babson-green) !important;
  background: var(--babson-green-light) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--babson-green) !important;
  border-bottom-color: var(--babson-green) !important;
  background: transparent !important;
}
/* Tab highlight bar */
div[data-baseweb="tab-highlight"] {
  background-color: var(--babson-green) !important;
}

/* ——— Radio pills (Source / Sort toolbar) ——— */
div[role="radiogroup"] > label {
  font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
  font-weight: 500;
  font-size: .85rem !important;
  text-transform: uppercase;
  letter-spacing: .4px;
  background: var(--neutral-100);
  border: 1px solid var(--neutral-200);
  border-radius: 999px;
  padding: 5px 14px;
  margin-right: 6px;
  cursor: pointer;
  transition: all .15s ease-in-out;
  color: var(--neutral-600);
}
div[role="radiogroup"] > label:hover {
  background: var(--babson-green-light);
  border-color: var(--babson-green);
  color: var(--babson-green);
}
div[role="radiogroup"] > label[data-checked="true"] {
  background: var(--babson-green) !important;
  color: #fff !important;
  border-color: var(--babson-green) !important;
}

/* ——— Form labels ——— */
.stRadio > label, .stCheckbox > label, .stSelectbox > label, .stTextInput > label {
  font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
  font-weight: 600;
  font-size: .88rem !important;
  text-transform: uppercase;
  letter-spacing: .3px;
  color: var(--neutral-600);
}

/* ——— Text inputs & selects — green focus ring ——— */
input[type="text"]:focus, div[data-baseweb="select"] > div:focus-within {
  border-color: var(--babson-green) !important;
  box-shadow: 0 0 0 1px var(--babson-green) !important;
}

/* ——— Checkbox accent ——— */
.stCheckbox input:checked + div svg { color: var(--babson-green) !important; }

/* ——— Faculty cards ——— */
.faculty-card {
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 6px;
  background: #ffffff;
  border: 1px solid var(--neutral-200);
  border-left: 4px solid var(--babson-green);
  transition: box-shadow .15s ease, border-color .15s ease;
}
.faculty-card:hover {
  box-shadow: 0 2px 8px rgba(0,102,68,.10);
  border-left-color: var(--mango-punch);
}
.faculty-card strong {
  font-family: 'Zilla Slab', Georgia, serif;
  font-weight: 600;
  font-size: .98rem;
  color: var(--babson-green-dark);
}
.faculty-card small {
  font-family: 'Zilla Slab', Georgia, serif;
  color: var(--neutral-400);
  font-size: .82rem;
  line-height: 1.35;
}

/* ——— Download button ——— */
.stDownloadButton > button {
  font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .4px;
  font-size: .82rem !important;
  background: var(--babson-green) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 4px !important;
  padding: .45rem 1.2rem !important;
  transition: background .15s ease;
}
.stDownloadButton > button:hover {
  background: var(--babson-green-dark) !important;
}

/* ——— Selectbox styling ——— */
div[data-baseweb="select"] {
  font-family: 'Zilla Slab', Georgia, serif !important;
}

/* ——— Section divider ——— */
hr {
  border: none;
  border-top: 1px solid var(--neutral-200);
  margin: 1.5rem 0 .8rem;
}

/* ——— Footer caption ——— */
.stCaption, caption, .caption {
  font-family: 'Zilla Slab', Georgia, serif !important;
  font-size: .78rem !important;
  color: var(--neutral-400) !important;
}

/* ——— Info boxes ——— */
div[data-testid="stAlert"] {
  border-left-color: var(--babson-green) !important;
  background: var(--babson-green-light) !important;
}

/* ——— Reduce vertical gaps between stacked widgets ——— */
div[data-testid="stVerticalBlock"] > div:has(> label) { margin-bottom: .35rem; }

/* ——— Bold text uses brand green ——— */
.stMarkdown strong { color: var(--babson-green-dark); }

/* ——— Floating Chat Widget ——— */
.chat-fab {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 99999;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #006644;
  color: #fff;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,.25);
  font-size: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background .15s ease, transform .15s ease, box-shadow .15s ease;
}
.chat-fab:hover {
  background: #004d33;
  transform: scale(1.07);
  box-shadow: 0 6px 20px rgba(0,0,0,.3);
}
.chat-fab.open { display: none; }

.chat-panel {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 99999;
  width: 400px;
  height: 560px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,.22);
  display: none;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e4e7eb;
}
.chat-panel.open { display: flex; }

.chat-panel-header {
  background: #006644;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 3px solid #EEAF00;
  flex-shrink: 0;
}
.chat-panel-header .chat-title {
  font-family: 'Oswald', 'Arial Narrow', sans-serif;
  font-weight: 600;
  font-size: .95rem;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: .5px;
  margin: 0;
}
.chat-panel-header .chat-subtitle {
  font-family: 'Zilla Slab', Georgia, serif;
  font-size: .72rem;
  color: rgba(255,255,255,.7);
  margin: 2px 0 0 0;
}
.chat-panel-close {
  background: none;
  border: none;
  color: rgba(255,255,255,.8);
  font-size: 22px;
  cursor: pointer;
  padding: 0 0 0 12px;
  line-height: 1;
  transition: color .12s ease;
}
.chat-panel-close:hover { color: #fff; }

.chat-panel-body {
  flex: 1;
  min-height: 0;
}
.chat-panel-body iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
""", unsafe_allow_html=True)

# ——— Brand header bar ———
st.markdown("""
<div class="brand-bar">
  <h1>Babson Faculty Research Interest Explorer</h1>
  <div class="subtitle">Explore faculty by topic or person. Use keywords, categories, profile interests, or all combined.</div>
</div>
""", unsafe_allow_html=True)

# ——— Floating Chat Widget ———
COPILOT_IFRAME_URL = "https://copilotstudio.microsoft.com/environments/Default-e83d2ad7-3bcd-4d5c-9d6c-6ffa1a4434bf/bots/copilots_header_c9faf/webchat?__version__=2"

st.markdown(f"""
<button class="chat-fab" id="chatFab" onclick="document.getElementById('chatPanel').classList.add('open'); this.classList.add('open');" title="Ask the Research Assistant">
  &#x1F4AC;
</button>

<div class="chat-panel" id="chatPanel">
  <div class="chat-panel-header">
    <div>
      <div class="chat-title">Research Assistant</div>
      <div class="chat-subtitle">Ask about faculty expertise &amp; research</div>
    </div>
    <button class="chat-panel-close" onclick="document.getElementById('chatPanel').classList.remove('open'); document.getElementById('chatFab').classList.remove('open');" title="Close">&#x2715;</button>
  </div>
  <div class="chat-panel-body">
    <iframe src="{COPILOT_IFRAME_URL}" allow="microphone;"></iframe>
  </div>
</div>
""", unsafe_allow_html=True)

DATA_PATH = "faculty_research_mapping_source.csv"

# =========================
# Helpers
# =========================
def parse_listish(value, split_chars=",;"):
    """Accept comma/semicolon lists or python-list strings (robust to earlier exports)."""
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    s = str(value).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
    parts = re.split(rf"\s*[{re.escape(split_chars)}]\s*", s)
    return [p for p in (x.strip() for x in parts) if p]

def get_row_topics(source: str, row: pd.Series):
    if source == "Profile":
        return row["Profile_list"]
    if source == "Categories":
        return row["Categories_list"]
    if source == "Keywords":
        return row["Keywords_list"]
    # "All"
    return sorted(set(row["Profile_list"]) | set(row["Categories_list"]) | set(row["Keywords_list"]))

# =========================
# Data loading
# =========================
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = None
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except Exception as e:
            last_err = e
    if df is None:
        st.error(f"Unable to read CSV at {path}. Last error: {last_err}")
        st.stop()

    expected = {"Faculty Name", "Profile Interests", "Categories", "All Keywords"}
    missing = expected - set(df.columns)
    if missing:
        st.error(f"CSV missing required columns: {', '.join(sorted(missing))}")
        st.stop()

    # Parse to lists (works on already-clean comma-separated strings)
    df["Profile_list"]    = df["Profile Interests"].apply(parse_listish)
    df["Categories_list"] = df["Categories"].apply(parse_listish)
    df["Keywords_list"]   = df["All Keywords"].apply(parse_listish)

    # For display
    df["Profile_display"]    = df["Profile_list"].apply(lambda xs: ", ".join(xs))
    df["Categories_display"] = df["Categories_list"].apply(lambda xs: ", ".join(xs))
    df["Keywords_display"]   = df["Keywords_list"].apply(lambda xs: ", ".join(xs))
    return df

df = load_data(DATA_PATH)

# =========================
# Tabs
# =========================
tab_topic, tab_faculty = st.tabs(["By Topic", "By Faculty Member"])

# =========================
# BY TOPIC
# =========================
with tab_topic:
    # Toolbar — single row
    c1, c2, c3, c4 = st.columns([2.6, 1.2, 1.2, 2.0])
    with c1:
        source = st.radio(
            "Source",
            ["Profile", "Categories", "Keywords", "All"],
            index=2,  # default to Keywords
            horizontal=True,
            help=(
                "Profile Interests → Sourced from Digital Measures.\n"
                "Categories, Keywords → AI-Generated Summary based on Faculty Page."
            ),
        )
    with c2:
        sort_mode = st.radio("Sort", ["Count", "A–Z"], index=0, horizontal=True)
    with c3:
        hide_singletons = st.checkbox("Hide singles", value=True, help="Hide topics with only one faculty")
    with c4:
        topic_search = st.text_input("Search", "", placeholder="Filter topics…").strip().lower()

    # Build topic universe & counts
    topic_series = df.apply(lambda r: get_row_topics(source, r), axis=1)
    all_topics = [t for topics in topic_series for t in topics]
    counts = Counter([t for t in all_topics if topic_search in t.lower()])

    items = list(counts.items())
    if sort_mode == "Count":
        items = sorted(items, key=lambda x: (-x[1], x[0].lower()))
    else:
        items = sorted(items, key=lambda x: x[0].lower())
    if hide_singletons:
        items = [(t, n) for t, n in items if n > 1]

    # Topic selector
    topic_labels = [f"{t} ({n})" for t, n in items]
    lookup = {f"{t} ({n})": t for t, n in items}

    if topic_labels:
        selected_label = st.selectbox("Topic", topic_labels, key="topic_select")
        selected_topic = lookup[selected_label]

        # Matches
        matches_mask = topic_series.apply(lambda xs: selected_topic in xs)
        matches = df[matches_mask]

        st.subheader(f"Faculty for: _{selected_topic}_")
        if matches.empty:
            st.info("No faculty found.")
        else:
            for _, r in matches.sort_values("Faculty Name").iterrows():
                st.markdown(f"""
<div class="faculty-card">
  <strong>{r['Faculty Name']}</strong><br>
  <small>{r['Categories_display']}</small>
</div>
""", unsafe_allow_html=True)

            # Download filtered results
            out = matches[["Faculty Name", "Profile_display", "Categories_display", "Keywords_display"]].rename(
                columns={
                    "Faculty Name": "Faculty",
                    "Profile_display": "Profile Interests",
                    "Categories_display": "Categories",
                    "Keywords_display": "All Keywords",
                }
            )
            st.download_button(
                "Download these results (CSV)",
                data=out.to_csv(index=False).encode("utf-8"),
                file_name="faculty_filtered_by_topic.csv",
                mime="text/csv",
            )
    else:
        st.info("No topics to display. Try clearing the search or toggling options.")

# =========================
# BY FACULTY
# =========================
with tab_faculty:
    f1, _ = st.columns([2, 3])
    with f1:
        f_search = st.text_input("Search faculty", "", placeholder="Name contains…").strip().lower()

    fac_list = df["Faculty Name"].tolist()
    if f_search:
        fac_list = [n for n in fac_list if f_search in n.lower()]
    fac_list = sorted(fac_list, key=str.lower)

    if not fac_list:
        st.info("No matching faculty. Clear the search to see all.")
    else:
        selected_faculty = st.selectbox("Faculty", fac_list, key="faculty_select")
        row = df[df["Faculty Name"] == selected_faculty].iloc[0]

        st.subheader(selected_faculty)
        st.markdown("**Profile Interests**")
        st.markdown(row["Profile_display"] or "_None_")
        st.markdown("**Categories**")
        st.markdown(row["Categories_display"] or "_None_")
        st.markdown("**All Keywords**")
        st.markdown(row["Keywords_display"] or "_None_")

        # Download single record
        out = pd.DataFrame([{
            "Faculty": selected_faculty,
            "Profile Interests": row["Profile_display"],
            "Categories": row["Categories_display"],
            "All Keywords": row["Keywords_display"],
        }])
        st.download_button(
            "Download this faculty (CSV)",
            data=out.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_faculty.replace(' ', '_')}_record.csv",
            mime="text/csv",
        )

# =========================
# Footnote
# =========================
st.markdown("---")
st.caption("**Data sources:** Profile Interests → *Sourced from Digital Measures*. "
           "Categories, Keywords → *AI-Generated Summary based on Faculty Page*.")
