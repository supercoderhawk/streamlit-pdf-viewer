import streamlit as st
import os
import sys

# Add parent directory to path to import streamlit_pdf_viewer_plus
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from streamlit_pdf_viewer_plus import pdf_viewer

st.set_page_config(page_title="Toolbar Sticky Test", layout="wide")

st.title("PDF Viewer Toolbar Sticky Test")

st.write("""
This test specifically checks if the PDF toolbar remains visible (sticky) when scrolling within Streamlit containers.

### Test Instructions:
1. Scroll down within the PDF container below
2. The toolbar (with navigation and zoom controls) should remain visible at the top
3. Try different container heights to verify the fix works in various scenarios
""")

# Load test PDF
try:
    with open("../../resources/test.pdf", 'rb') as fo:
        binary = fo.read()
        
    # Test 1: Small container height (should force scrolling)
    st.write("## Test 1: Small Container (height=300px)")
    st.write("*Scroll within this container - toolbar should stay visible*")
    with st.container(height=300):
        pdf_viewer(
            binary,
            annotations=[],
            render_text=True,
            key="test_small",
            width="100%"
        )
    
    # Test 2: Medium container height
    st.write("## Test 2: Medium Container (height=500px)")
    st.write("*Scroll within this container - toolbar should stay visible*")
    with st.container(height=500):
        pdf_viewer(
            binary,
            annotations=[],
            render_text=True,
            key="test_medium",
            width="100%"
        )
    
    # Test 3: No container (full height)
    st.write("## Test 3: No Container Restriction")
    st.write("*Toolbar should be visible without container restrictions*")
    pdf_viewer(
        binary,
        annotations=[],
        render_text=True,
        key="test_full",
        width="100%"
    )

except FileNotFoundError:
    st.error("Test PDF file not found at '../../resources/test.pdf'")
    st.write("Please ensure the test PDF file exists in the resources directory")
