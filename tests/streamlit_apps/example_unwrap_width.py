import os

import streamlit as st
from tests import ROOT_DIRECTORY

from streamlit_pdf_viewer_plus import pdf_viewer

st.subheader("Test PDF Viewer with arguments with specified width")

pdf_viewer(os.path.join(ROOT_DIRECTORY, "resources/test.pdf"), width=400)
