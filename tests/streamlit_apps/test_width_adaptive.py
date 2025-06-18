import streamlit as st
import streamlit_pdf_viewer as pdf_viewer
import base64

st.set_page_config(page_title="PDF Width Adaptive Test", layout="wide")

st.title("PDF宽度自适应测试")

# 读取测试PDF文件
try:
    with open("resources/test.pdf", "rb") as f:
        binary_data = f.read()
        binary_data_base64 = base64.b64encode(binary_data).decode('utf-8')
        
    st.write("## 测试1: 不指定宽度 (应该占满容器)")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        key="test1"
    )
    
    st.write("## 测试2: 指定50%宽度")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        width="50%",
        key="test2"
    )
    
    st.write("## 测试3: 指定800px宽度")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        width=800,
        key="test3"
    )
    
    st.write("## 测试4: 100%宽度")
    pdf_viewer.pdf_viewer(
        input=binary_data,
        rendering='unwrap',
        width="100%",
        key="test4"
    )

except FileNotFoundError:
    st.error("找不到测试PDF文件 'resources/test.pdf'")
    st.write("请确保测试PDF文件存在")
