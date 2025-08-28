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
/* Wider but readable page + a touch more top padding */
.block-container { max-width: 1100px; padding-top: 1.2rem; padding-bottom: 1.6rem; }

/* Softer title + subtitle spacing */
h1 { margin-bottom: .25rem !important; letter-spacing: .2px; }
.subtitle { color: #666; margin: 0 0 1rem 2px; }

/* Toolbar pills (radios) — use theme primary color */
div[role="radiogroup"] > label {
  background: #f4f6f8;
  border: 1px solid #e6e8eb;
  border-radius: 999px;
  padding: 4px 12px;
  margin-right: 6px;
  cursor: pointer;
  transition: all .12s ease-in-out;
  font-weight: 600;
}
div[role="radiogroup"] > label:hover { background: #eef2f5; }
div[role="radiogroup"] > label[data-checked="true"] {
  background: var(--primary-color);
  color: #fff;
  border-color: var(--primary-color);
}

/* Compact labels */
.stRadio > label, .stCheckbox > label, .stSelectbox > label, .stTextInput > label { font-weight: 600; }
label { font-size: .92rem !important; }

/* Cards for faculty list */
.faculty-card {
  padding: 10px 12px;
  margin: 6px 0;
  border-radius: 10px;
  background: #fafbfc;
  border: 1px solid #edf0f3;
}
.faculty-card strong { font-weight: 700; }
.faculty-card small { color: #6b7280; }

/* Reduce vertical gaps between stacked widgets */
div[data-testid="stVerticalBlock"] > div:has(> label) { margin-bottom: .35rem; }

/* Section headers tighter */
h3 { margin-top: .6rem !important; }
</style>
""", unsafe_allow_html=True)

st.header("Babson Faculty Research Interest Explorer")
st.markdown(
    '<div class="subtitle">Explore faculty by topic or person. Use keywords, categories, profile interests, or all combined.</div>',
    unsafe_allow_html=True
)

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
        sort_mode = st.radio("Sort", ["Count", "Alphabetical"], index=0, horizontal=True)
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
