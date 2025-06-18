import streamlit as st
import streamlit_pdf_viewer as pdf_viewer
import base64

st.set_page_config(page_title="PDF Width Adaptive Test", layout="wide")

st.title("PDF Width Adaptive Test")

# Read test PDF file
try:
    with open("resources/test.pdf", "rb") as f:
        binary_data = f.read()
        binary_data_base64 = base64.b64encode(binary_data).decode('utf-8')
        
    st.write("## Test 1: No width specified (should fill container)")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        annotations=[],
        key="test1"
    )
    
    st.write("## Test 2: 50% width specified")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        width="50%",
        annotations=[],
        key="test2"
    )
    
    st.write("## Test 3: 800px width specified")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        width=800,
        annotations=[],
        key="test3"
    )
    
    st.write("## Test 4: 100% width")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        width="100%",
        annotations=[],
        key="test4"
    )

except FileNotFoundError:
    st.error("Test PDF file 'resources/test.pdf' not found")
    st.write("Please ensure the test PDF file exists")
