import streamlit as st

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

if st.button("Analyze Case"):
    st.success("Case received successfully.")

st.divider()

st.subheader("Extracted Facts")
st.write("Crime Type: -")
st.write("Technology: -")
st.write("Evidence Type: -")

st.divider()

st.subheader("Applicable Laws")
st.write("-")

st.divider()

st.subheader("Evidence Considerations")
st.write("-")