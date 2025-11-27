import streamlit as st
import pdfplumber
import pandas as pd
import io
import re
from docx import Document

# --- App Configuration ---
st.set_page_config(page_title="Multi-Document KSB Mapper", layout="wide")

st.title("📚 Multi-Document Student KSB Mapper")
st.markdown("""
Upload multiple student documents (PDF or Word), enter their respective KSBs, 
and generate one consolidated mapping document.
""")

# --- Sidebar: Uploads ---
st.sidebar.header("1. Upload Documents")
uploaded_files = st.sidebar.file_uploader(
    "Upload student documents (PDF or Word)", 
    type=['pdf', 'docx'], 
    accept_multiple_files=True
)

# --- Sidebar: KSBs per file ---
file_ksb_map = {}
if uploaded_files:
    st.sidebar.header("2. Define KSBs per file")
    for file in uploaded_files:
        ksb_input = st.sidebar.text_area(
            f"KSBs for {file.name}", 
            placeholder="K1\nK2\nS1\nB1"
        )
        file_ksb_map[file.name] = [x.strip() for x in ksb_input.split('\n') if x.strip()]

# --- Helper Functions ---
def extract_mappings_pdf(file, search_terms, doc_title):
    results = []
    with pdfplumber.open(file) as pdf:
        total_pages = len(pdf.pages)
        progress_bar = st.progress(0)

        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                for term in search_terms:
                    pattern = r'\b' + re.escape(term) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        results.append({
                            "Document": doc_title,
                            "KSB Reference": term,
                            "Page Number": i + 1
                        })
            progress_bar.progress((i + 1) / total_pages)
    return results

def extract_mappings_docx(file, search_terms, doc_title):
    results = []
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    for term in search_terms:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            results.append({
                "Document": doc_title,
                "KSB Reference": term,
                "Page Number": "N/A (Word)"
            })
    return results

# --- Main Execution ---
if st.button("Generate Consolidated Mapping", type="primary"):
    if not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        all_results = []
        with st.spinner("Scanning all documents..."):
            try:
                for file in uploaded_files:
                    ksb_list = file_ksb_map.get(file.name, [])
                    if not ksb_list:
                        continue

                    if file.name.endswith(".pdf"):
                        file.seek(0)
                        mappings = extract_mappings_pdf(file, ksb_list, file.name)
                    elif file.name.endswith(".docx"):
                        file.seek(0)
                        mappings = extract_mappings_docx(file, ksb_list, file.name)
                    else:
                        mappings = []

                    all_results.extend(mappings)

                if all_results:
                    df = pd.DataFrame(all_results)
                    df = df.sort_values(by=['Document', 'KSB Reference'])

                    st.success(f"Found {len(df)} matches across {len(uploaded_files)} documents!")
                    st.dataframe(df, use_container_width=True)

                    # Export consolidated results
                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Consolidated Mapping')

                    st.download_button(
                        label="📥 Download Consolidated Mapping (.xlsx)",
                        data=output_excel.getvalue(),
                        file_name="All_KSB_Mappings.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    st.download_button(
                        label="📥 Download Consolidated Mapping (.csv)",
                        data=df.to_csv(index=False).encode('utf-8'),
                        file_name="All_KSB_Mappings.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No KSBs found in the uploaded documents.")

            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- Instructions Footer ---
st.markdown("---")
st.markdown("### How to use this app:")
st.markdown("""
1. **Upload Documents:** Add multiple PDFs or Word files in the sidebar.  
2. **Enter KSBs:** For each file, paste the relevant KSB codes.  
3. **Generate:** Click the button to scan all documents.  
4. **Download:** Export one consolidated mapping document in Excel or CSV.  
""")

