import streamlit as st

# from src.modules.login_page import check_password

st.set_page_config(
    page_title=st.secrets["entreprise_nom"], page_icon="🚗", layout="wide"
)

# if not check_password():
#    st.stop()

page_devis = st.Page(
    "src/pages/devis_facture.py",
    title="Devis / Facture",
    icon="🧾",
    default=True,
    url_path="devis-facture",
)

navigation = st.navigation([page_devis])

st.sidebar.image("imgs/logo.png", width=200)

navigation.run()
