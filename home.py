import streamlit as st
import os
import importlib.util
import sys

st.set_page_config(page_title="SDLC Gen-AI", layout="wide", page_icon="⚡")

st.sidebar.title("⚡ Agent Factory")
selection = st.sidebar.radio("Go to:", ["🏠 Home", "🏗️ Plan Agent", "🎨 Design Agent"])

if selection == "🏠 Home":
    st.title("Welcome to IPS Software Factory")
    st.markdown("Select an Agent from the sidebar to begin.")

elif selection == "🏗️ Plan Agent":
    # Execute p1/app.py
    file_path = os.path.join(os.getcwd(), "p1", "app.py")
    spec = importlib.util.spec_from_file_location("p1_app", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["p1_app"] = module
    spec.loader.exec_module(module)
    module.main()

elif selection == "🎨 Design Agent":
    # Execute p1/bpp.py
    file_path = os.path.join(os.getcwd(), "p1", "bpp.py")
    spec = importlib.util.spec_from_file_location("p1_bpp", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["p1_bpp"] = module
    spec.loader.exec_module(module)

    module.main()
