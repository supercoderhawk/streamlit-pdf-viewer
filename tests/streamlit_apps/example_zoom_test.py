import os

import streamlit as st

from streamlit_pdf_viewer import pdf_viewer
from tests import ROOT_DIRECTORY

st.title("PDF Viewer 缩放功能测试")

st.subheader("PDF 查看器 - 缩放功能演示")
st.write("这个示例展示了新添加的缩放功能:")
st.write("- 使用 + 按钮放大PDF")
st.write("- 使用 - 按钮缩小PDF")
st.write("- 显示当前缩放百分比")
st.write("- 使用'重置'按钮恢复到100%缩放")

# 使用unwrap渲染模式以启用缩放功能
pdf_viewer(
    os.path.join(ROOT_DIRECTORY, "resources/test.pdf"),
    rendering="unwrap",
    width=700,
    height=400
)

st.subheader("功能说明")
st.markdown("""
### 缩放控件说明:
- **-** 按钮: 缩小PDF (最小50%)
- **+** 按钮: 放大PDF (最大300%)
- **数字显示**: 当前缩放百分比
- **重置** 按钮: 恢复到100%缩放

### 使用提示:
1. 点击 + 或 - 按钮进行缩放
2. 缩放后页面会自动重新渲染
3. 当前页面位置会保持不变
4. 缩放范围: 50% - 300%
""")
