import streamlit as st
import os
import sys

# Add parent directory to path to import streamlit_pdf_viewer_plus
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from streamlit_pdf_viewer_plus import pdf_viewer

st.set_page_config(page_title="Page Navigation Bug Test", layout="wide")

st.title("PDF Viewer Page Navigation Bug Test")

st.write("""
This test specifically checks the bug where:
1. On the last page, the "Next Page" button should be disabled
2. Page number should not jump to 1 when clicking disabled buttons
3. Manual page input should be validated and constrained

### Test Instructions:
1. Navigate to the last page using the navigation controls
2. Try clicking the "Next Page" button (should be disabled)
3. Try manually entering invalid page numbers
4. Verify the page number stays consistent
""")

# Load test PDF
try:
    with open("../../resources/test.pdf", 'rb') as fo:
        binary = fo.read()
        
    st.write("## PDF Viewer Test")
    st.write("*Navigate to the last page and test the navigation controls*")
    
    with st.container(height=500):
        viewer = pdf_viewer(
            binary,
            annotations=[],
            render_text=True,
            key="page_nav_test",
            width="100%"
        )
    
    if viewer:
        st.write("### Debug Information:")
        st.write(f"Component returned value: {viewer}")
    
    st.write("### Expected Behavior:")
    st.write("- Navigation buttons should be properly disabled when at first/last page")
    st.write("- Page input should accept only valid page numbers")
    st.write("- Page number should never jump unexpectedly")

except FileNotFoundError:
    st.error("Test PDF file not found at '../../resources/test.pdf'")
    st.write("Please ensure the test PDF file exists in the resources directory")
