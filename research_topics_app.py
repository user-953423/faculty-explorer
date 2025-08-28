import streamlit as st
import pandas as pd
import ast
import re
from collections import Counter

# --------------------
# Page setup
# --------------------
st.set_page_config(page_title="Babson Faculty Research Explorer", layout="wide")
st.title("Babson Faculty Research Explorer")

DATA_PATH = "faculty_keywords_and_categories.csv"

@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    # Be forgiving on encodings
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except Exception:
            continue
    else:
        st.stop()

    # Normalize expected columns
    expected = {"Faculty Name", "Categories", "All Keywords"}
    missing = expected - set(df.columns)
    if missing:
        st.error(f"Missing columns in CSV: {', '.join(missing)}")
        st.stop()

    # Normalizers handle either comma-separated strings OR Python list strings
    def parse_listish(value, split_chars=","):
        if pd.isna(value):
            return []
        if isinstance(value, list):
            return [x.strip() for x in value if str(x).strip()]
        s = str(value).strip()
        # Try to parse a Python list string like "['A', 'B']"
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = ast.literal_eval(s)
                return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        # Fallback: split on the provided separators
        parts = re.split(rf"\s*[{re.escape(split_chars)};]\s*", s)
        return [p for p in (x.strip() for x in parts) if p]

    df["Categories_list"] = df["Categories"].apply(lambda v: parse_listish(v, split_chars=","))

    # All Keywords may be separated by semicolons or commas in your file
    df["Keywords_list"] = df["All Keywords"].apply(lambda v: parse_listish(v, split_chars=";,"))
    # Deduplicate within a person
    df["Categories_list"] = df["Categories_list"].apply(lambda xs: sorted(set(xs), key=str.lower))
    df["Keywords_list"] = df["Keywords_list"].apply(lambda xs: sorted(set(xs), key=str.lower))

    # For display / search convenience
    df["Categories_display"] = df["Categories_list"].apply(lambda xs: ", ".join(xs))
    df["Keywords_display"]  = df["Keywords_list"].apply(lambda xs: ", ".join(xs))

    return df

df = load_data(DATA_PATH)

# --------------------
# Sidebar filters
# --------------------
st.sidebar.header("Filters")

# Category universe (sorted by frequency then alpha)
all_cats = [c for xs in df["Categories_list"] for c in xs]
cat_counts = Counter(all_cats)
sorted_cats = [c for c, _ in sorted(cat_counts.items(), key=lambda x: (-x[1], x[0].lower()))]

# Keyword universe (optional browse list; free text search is primary)
all_keywords = [k for xs in df["Keywords_list"] for k in xs]
kw_counts = Counter(all_keywords)
sorted_kws = [k for k, _ in sorted(kw_counts.items(), key=lambda x: (-x[1], x[0].lower()))]

filter_mode = st.sidebar.radio(
    "Explore mode",
    ["By Category", "By Keyword", "Combined (Category + Keyword)"],
    index=0
)

if filter_mode in ("By Category", "Combined (Category + Keyword)"):
    selected_categories = st.sidebar.multiselect(
        "Categories",
        options=sorted_cats,
        default=[],
        help="Select one or more categories to filter faculty."
    )
else:
    selected_categories = []

if filter_mode in ("By Keyword", "Combined (Category + Keyword)"):
    keyword_query = st.sidebar.text_input(
        "Keyword search",
        value="",
        placeholder="e.g., retail, supply chain, behavioral finance…"
    ).strip()
else:
    keyword_query = ""

exact_keyword_match = st.sidebar.checkbox(
    "Exact keyword match",
    value=False,
    help="When on, matches must equal a full keyword; when off, partial substring matches are allowed."
)

hide_singletons = st.sidebar.checkbox(
    "Hide keywords with only one faculty (counts list & suggestions)",
    value=False
)

# --------------------
# Filtering logic
# --------------------
def match_categories(row) -> bool:
    if not selected_categories:
        return True
    row_cats = set(row["Categories_list"])
    # Faculty passes if they have ANY of the selected categories
    return bool(row_cats.intersection(selected_categories))

def match_keywords(row) -> bool:
    if not keyword_query:
        return True
    query = keyword_query.lower()
    # Exact match searches within discrete keyword tokens
    if exact_keyword_match:
        return any(k.lower() == query for k in row["Keywords_list"])
    # Substring: check any keyword contains the query
    return any(query in k.lower() for k in row["Keywords_list"])

mask = df.apply(lambda r: match_categories(r) and match_keywords(r), axis=1)
filtered = df[mask].copy()

# --------------------
# Header metrics
# --------------------
colA, colB, colC, colD = st.columns(4)
colA.metric("Faculty (filtered)", f"{len(filtered):,}")
colB.metric("Total Categories", f"{len(cat_counts):,}")
colC.metric("Total Keywords", f"{len(kw_counts):,}")
colD.metric("CSV Rows", f"{len(df):,}")

# --------------------
# Suggested facets (left column) + Results (right)
# --------------------
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Top Categories")
    counts_view = cat_counts.copy()
    # Show top categories overall or within current keyword filter
    if keyword_query:
        # Recompute cat counts based on keyword filter only
        subset = df[df.apply(match_keywords, axis=1)]
        counts_view = Counter([c for xs in subset["Categories_list"] for c in xs])
    top_cats = sorted(counts_view.items(), key=lambda x: (-x[1], x[0].lower()))
    if hide_singletons:
        top_cats = [(c, n) for c, n in top_cats if n > 1]
    if top_cats:
        st.write("\n".join([f"- **{c}** ({n})" for c, n in top_cats[:30]]))
    else:
        st.caption("_No categories to show._")

    st.subheader("Top Keywords")
    kw_view = kw_counts.copy()
    if selected_categories:
        # Recompute keyword counts based on category filter only
        subset = df[df.apply(match_categories, axis=1)]
        kw_view = Counter([k for xs in subset["Keywords_list"] for k in xs])
    top_kws = sorted(kw_view.items(), key=lambda x: (-x[1], x[0].lower()))
    if hide_singletons:
        top_kws = [(k, n) for k, n in top_kws if n > 1]
    if top_kws:
        st.write("\n".join([f"- **{k}** ({n})" for k, n in top_kws[:50]]))
    else:
        st.caption("_No keywords to show._")

with right:
    st.subheader("Results")
    if filtered.empty:
        st.info("No matches. Try removing some filters or toggling exact match.")
    else:
        # Nice, compact view
        show_cols = ["Faculty Name", "Categories_display", "Keywords_display"]
        renamed = filtered[show_cols].rename(columns={
            "Faculty Name": "Faculty",
            "Categories_display": "Categories",
            "Keywords_display": "All Keywords"
        })
        st.dataframe(
            renamed,
            use_container_width=True,
            hide_index=True
        )

        # Download filtered set
        csv_bytes = renamed.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered results (CSV)",
            data=csv_bytes,
            file_name="faculty_filtered.csv",
            mime="text/csv"
        )

# --------------------
# Footnotes
# --------------------
st.caption("Tip: Use **Combined** mode to filter by Categories and refine with a keyword at the same time. "
           "Partial matches are allowed unless you toggle **Exact keyword match**.")
