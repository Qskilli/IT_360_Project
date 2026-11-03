import streamlit as st

from src.database import get_all_laws
from src.ai_client import analyze_case, AIError

st.set_page_config(
    page_title="Digital Forensics Law Detector",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Digital Forensics Law Detector")

st.write(
    "Analyze a case description and identify potentially relevant laws."
)

case_description = st.text_area(
    "Case Description",
    height=250,
    placeholder="Describe the investigation..."
)

result = None

if st.button("Analyze Case"):

    try:
        laws = get_all_laws()

        result = analyze_case(
            case_description,
            laws
        )

        st.success(
            f"Case analyzed successfully. ({len(laws)} laws loaded)"
        )

    except AIError as error:
        st.error(str(error))

    except Exception as error:
        st.error(f"Unexpected error: {error}")

st.divider()

st.subheader("Extracted Facts")

if result:

    facts = result.get("facts", {})

    st.write(
        f"Crime Type: {facts.get('crime_type', 'Unknown')}"
    )

    st.write(
        f"Technology: {facts.get('technology', 'Unknown')}"
    )

    st.write(
        f"Evidence Type: {facts.get('evidence_type', 'Unknown')}"
    )

else:
    st.write("Click Analyze Case to view results.")

st.divider()

st.subheader("Applicable Laws")

if result and result.get("laws"):

    for law in result["laws"]:

        st.write(
            f"**{law.get('title', 'Unknown Law')}**"
        )

        st.write(
            law.get("reason", "")
        )

else:
    st.write("-")

st.divider()

st.subheader("Evidence Considerations")

if result and result.get("evidence_considerations"):

    for consideration in result["evidence_considerations"]:
        st.write(f"• {consideration}")

else:
    st.write("-")