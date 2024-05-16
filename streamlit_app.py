import streamlit as st
from num2words import num2words

from src.modules.reference import get_reference
from src.modules.tab_prestations import tab_prestations
from src.modules.pdf_generator import DEVIS_FACTURE, create_download_link
from src.modules.login_page import check_password

if not check_password():
    st.stop()

st.set_page_config(page_title=st.secrets["nom_ent"], page_icon="💻", layout="wide")
st.title(f"🚗 {st.secrets.nom_ent} :red[DEVIS] et :blue[FACTURE]")

st.sidebar.image("imgs/as_auto.png", width=200)

type_document = st.sidebar.selectbox(
    "Choisir le type de document voulu.",
    ("Devis", "Facture"),
    key="type_document",
    help="Attention à ne pas se tromper de type de document ! ",
)

date = st.sidebar.date_input("Date du document :", format="DD/MM/YYYY")
st.sidebar.title(
    "Informations Client:",
    help="Ici il faut remplir les informations du client.",
)
nom = st.sidebar.text_input("Nom:", key="nom")
prenom = st.sidebar.text_input("Prénom:", key="prenom")
telephone = st.sidebar.text_input("Tél:", key="telephone")
email = st.sidebar.text_input("Email:", key="email")
adresse = st.sidebar.text_input("Adresse postale:", key="adresse")


col_voit, col_vide, col_prest = st.columns(spec=[0.15, 0.01, 0.84])

with col_voit:
    st.title("Info voiture:", help="Ici il faut remplir les informations du véhicule.")
    marque = st.text_input("Marque", key="marque")
    modele = st.text_input("Modèle", key="modele")
    immatriculation = st.text_input("Immatriculation", key="immatriculation")
    nserie = st.text_input("Numéro de série", key="nserie")
    kilometrage = st.number_input(
        "Kilométrage",
        min_value=0,
        max_value=2000000,
        step=10000,
        value=100000,
        key="kilometrage",
    )

with col_prest:
    st.title(
        "Prestations effectué",
        help="Ici il faut ajouter ce qui a été fait sur le véhicule, ATTENTION ⚠️, seul le Total 💸 compte dans ce tableau, le prix et la quantité sont la juste pour l'esthétique du tableau.",
    )

    with st.container():
        df = tab_prestations()
        st.session_state["prestations"] = df
        data = st.session_state["prestations"]

    ajout_signature = st.checkbox(
        "Ajouter les signatures.",
        help="En cliquant sur la case, le document contiendra à la fin un texte pour que les deux parties le signent.",
    )
    generate_doc = st.button("Générer document")
    if generate_doc:
        st.session_state["montant_total_output"] = str(
            format(round(df["total_prest"].sum(skipna=True), 2), ".2f")
            + " euros ("
            + str(
                num2words(
                    round(df["total_prest"].sum(skipna=True), 2),
                    to="currency",
                    lang="fr",
                )
            )
            + ")"
        )
        st.write(f"TOTAL : {st.session_state["montant_total_output"]}")
        st.session_state["ref"] = get_reference(st.session_state)
        try:
            pdf = DEVIS_FACTURE(st.session_state, st.secrets)
            pdf.add_page()
            pdf.entete()
            pdf.info_voitures()
            pdf.tableau_prestations()
            pdf.total_document()
            if ajout_signature:
                pdf.signatures()
            html = create_download_link(
                pdf.output(dest="S").encode("latin-1"), st.session_state["ref"]
            )
            st.markdown(html, unsafe_allow_html=True)
        except RecursionError as e:
            st.error(
                f"""
                Erreur lors de la génération du fichier, il y a trop de prestations, la limite est de 7. 
                {e}""",
                icon="🚨",
            )
