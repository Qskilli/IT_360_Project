import streamlit as st

from src.database import get_all_laws
from src.ai_client import analyze_case, AIError


st.markdown("""
<style>

/* Text area background */
textarea {
    background-color: #111827 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)




st.markdown("""
<style>
.stApp {
    background-color: #1f2937;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* Main background */
.stApp {
    background-color: #1f2937;
}

/* Text area styling */
textarea {
    background-color: #111827 !important;
    color: white !important;
    border: 1px solid white !important;
}

/* White outline when selected/focused */
textarea:focus {
    border: 2px solid white !important;
    box-shadow: 0 0 0 1px white !important;
    outline: none !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* Analyze button */
[data-testid="stButton"] button {
    border: 1px solid white !important;
    border-radius: 8px !important;
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="Digital Forensics Law Detector",
    page_icon="⚖️",
    layout="wide"
)

st.title("Digital Forensics Law Detector ⚖️  ")

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

    if not case_description.strip():
        st.error(
            "Please enter a case description before analyzing."
        )

    elif len(case_description.split()) < 20:
        st.error(
            "Please enter a more detailed case description (minimum 20 words)."
        )

    else:

        try:
            laws = get_all_laws()

            result = analyze_case(
                case_description,
                laws
            )

            st.success(
                f"Laws Loaded successfully. ({len(laws)} laws loaded)"
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