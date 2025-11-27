import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

# --- App Configuration ---
st.set_page_config(page_title="Student KSB Mapper", layout="wide")

st.title("🎓 Student Assignment Mapper")
st.markdown("""
This tool scans your **Main Document** for specific **KSB references** 
and generates a mapping matrix automatically.
""")

# --- Sidebar: Inputs ---
st.sidebar.header("1. Project Details")
unit_name = st.sidebar.text_input("Unit Name/Code", placeholder="e.g. Unit 5 - Leadership")
doc_title = st.sidebar.text_input("Document Title", placeholder="e.g. Portfolio Submission")

st.sidebar.header("2. Define KSBs")
st.sidebar.info("Enter the KSBs you want to search for (one per line).")
ksb_input_raw = st.sidebar.text_area("KSB List", placeholder="K1\nK2\nS1\nS4\nB1")

# Process KSB list into a clean list
ksb_list = [x.strip() for x in ksb_input_raw.split('\n') if x.strip()]

st.sidebar.header("3. Upload Document")
uploaded_file = st.sidebar.file_uploader("Upload Main Document (PDF only)", type=['pdf'])

# --- Logic Functions ---
def extract_mappings(file, search_terms):
    results = []
    with pdfplumber.open(file) as pdf:
        total_pages = len(pdf.pages)
        progress_bar = st.progress(0)

        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            text = page.extract_text()

            if text:
                for term in search_terms:
                    pattern = r'\b' + re.escape(term) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        results.append({
                            "Unit": unit_name,
                            "Title": doc_title,
                            "KSB Reference": term,
                            "Page Number": page_num
                        })

            progress_bar.progress((i + 1) / total_pages)

    return results

# --- Main Execution ---
if st.button("Generate Mapping Document", type="primary"):
    if not uploaded_file:
        st.error("Please upload a Main Document PDF.")
    elif not ksb_list:
        st.error("Please enter at least one KSB to search for.")
    else:
        with st.spinner("Scanning document..."):
            try:
                uploaded_file.seek(0)
                mappings = extract_mappings(uploaded_file, ksb_list)

                if mappings:
                    df = pd.DataFrame(mappings)
                    df = df.sort_values(by=['KSB Reference', 'Page Number'])

                    st.success(f"Found {len(df)} matches!")
                    st.dataframe(df, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Mapping')

                    st.download_button(
                        label="📥 Download Mapping (.xlsx)",
                        data=output.getvalue(),
                        file_name="KSB_Mapping_Document.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No KSBs found in the document. Check your spelling or file content.")

            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- Instructions Footer ---
st.markdown("---")
st.markdown("### How to use this app:")
st.markdown("""
1. **Enter Details:** Type the Unit and Title on the left.
2. **List KSBs:** Paste your specific KSB codes (e.g., `K5`, `S12`) on the left.
3. **Upload:** Drag and drop your assignment/thesis PDF.
4. **Generate:** Click the button to scan the PDF. The app will look for the exact text of your KSBs and tell you which page they are on.
""")
