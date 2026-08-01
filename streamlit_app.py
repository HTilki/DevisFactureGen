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
page_cession = st.Page(
    "src/pages/certificat_cession.py",
    title="Certificat de cession",
    icon="📄",
    url_path="certificat-cession",
)

navigation = st.navigation([page_devis, page_cession])

st.sidebar.image("imgs/logo.png", width=200)

navigation.run()
