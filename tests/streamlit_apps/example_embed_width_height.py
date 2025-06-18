import os

import streamlit as st

from streamlit_pdf_viewer_plus import pdf_viewer
from tests import ROOT_DIRECTORY

st.subheader("Test PDF Viewer using legacy embed with specified width and height")

pdf_viewer(os.path.join(ROOT_DIRECTORY, "resources/test.pdf"), rendering='legacy_embed', width=600, height=500)
