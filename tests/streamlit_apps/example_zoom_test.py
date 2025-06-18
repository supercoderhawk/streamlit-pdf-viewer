import os

import streamlit as st

from streamlit_pdf_viewer import pdf_viewer
from tests import ROOT_DIRECTORY

st.title("PDF Viewer Zoom Function Test")

st.subheader("PDF Viewer - Zoom Function Demo")
st.write("This example demonstrates the newly added zoom functionality:")
st.write("- Use the + button to zoom in on the PDF")
st.write("- Use the - button to zoom out of the PDF")
st.write("- Display current zoom percentage")
st.write("- Use the 'Reset' button to restore to 100% zoom")

# Use unwrap rendering mode to enable zoom functionality
pdf_viewer(
    os.path.join(ROOT_DIRECTORY, "resources/test.pdf"),
    rendering="unwrap",
    width=700,
    height=400
)

st.subheader("Feature Description")
st.markdown("""
### Zoom Control Description:
- **-** button: Zoom out PDF (minimum 50%)
- **+** button: Zoom in PDF (maximum 300%)
- **Number display**: Current zoom percentage
- **Reset** button: Restore to 100% zoom

### Usage Tips:
1. Click + or - buttons to zoom
2. Page will automatically re-render after zooming
3. Current page position will remain unchanged
4. Zoom range: 50% - 300%
""")
