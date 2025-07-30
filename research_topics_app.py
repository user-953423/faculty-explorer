import streamlit as st
import pandas as pd
import ast
from collections import Counter

# ---- Page setup ----
st.set_page_config(layout="centered")
st.title("Babson Faculty Research Interest Explorer")

# ---- Load data ----
df = pd.read_csv("Faculty - Research Interests.csv", encoding="latin1")

def parse_topics(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else []
    except:
        return []

df["Babson_Topics"] = df["Profile Interests - Cleaned"].apply(parse_topics)
df["OpenAlex_Topics"] = df["Publicly Available Interests"].apply(parse_topics)
df["Faculty_Label"] = df["Name"] + " <" + df["EMAIL"] + ">"

# ---- Mode switch ----
view_mode = st.radio("Choose how to explore:", ["By Topic", "By Faculty Member"])

show_openalex_footnote = False

# =====================
# === VIEW BY TOPIC ===
# =====================
if view_mode == "By Topic":
    source_option = st.radio("Select source of research interests:", [
        "Babson Profiles",
        "Public Database (OpenAlex)*",
        "Both"
    ])

    if "OpenAlex" in source_option:
        show_openalex_footnote = True

    def get_selected_topics(row):
        if source_option == "Babson Profiles":
            return row["Babson_Topics"]
        elif source_option == "Public Database (OpenAlex)*":
            return row["OpenAlex_Topics"]
        else:
            return list(set(row["Babson_Topics"]) | set(row["OpenAlex_Topics"]))

    df["Selected_Topics"] = df.apply(get_selected_topics, axis=1)

    all_topics = [topic for topics in df["Selected_Topics"] for topic in topics]
    topic_counts = Counter(all_topics)

    if st.checkbox("Hide topics with only one faculty member"):
        topic_counts = {k: v for k, v in topic_counts.items() if v > 1}

    sorted_topics = sorted(topic_counts.items(), key=lambda x: (-x[1], x[0]))
    topic_options = [f"{topic} ({count})" for topic, count in sorted_topics]
    topic_lookup = {label: topic for label, (topic, count) in zip(topic_options, sorted_topics)}

    if topic_options:
        selected_label = st.selectbox("Select a topic:", topic_options)
        query_topic = topic_lookup[selected_label]

        matches = df[df["Selected_Topics"].apply(lambda x: query_topic in x)]

        st.markdown(f"### Faculty associated with: *{query_topic}*")
        for _, row in matches.iterrows():
            st.write(f"- {row['Name']} ({row['EMAIL']})")
    else:
        st.info("No topics to display.")

# =========================
# === VIEW BY FACULTY  ====
# =========================
else:
    faculty_list = df["Faculty_Label"].tolist()
    selected_faculty = st.selectbox("Select a faculty member:", faculty_list)

    row = df[df["Faculty_Label"] == selected_faculty].iloc[0]

    st.subheader(f"Research Interests for {row['Name']}")

    # Link to OpenAlex profile if available
    if pd.notna(row.get("OpenAlex_ID")) and str(row["OpenAlex_ID"]).startswith("A"):
        openalex_url = f"https://openalex.org/{row['OpenAlex_ID']}"
        st.markdown(f"[View OpenAlex profile]({openalex_url})", unsafe_allow_html=True)
        show_openalex_footnote = True

    st.markdown("**Babson Profile Topics:**")
    if row["Babson_Topics"]:
        st.markdown(", ".join(row["Babson_Topics"]))
    else:
        st.markdown("_No topics listed in profile_")

    st.markdown("**Public Database (OpenAlex)* Topics:**")
    if row["OpenAlex_Topics"]:
        st.markdown(", ".join(row["OpenAlex_Topics"]))
    else:
        st.markdown("_No topics found in OpenAlex_")
    show_openalex_footnote = True  # Always show in faculty view

# ---- Footnote ----
if show_openalex_footnote:
    st.markdown("---")
    st.caption("*Public database (OpenAlex) profiles were matched using AI and may contain inaccuracies.")
