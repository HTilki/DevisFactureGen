import pandas as pd
import streamlit as st
from num2words import num2words

from src.modules.app_func import get_reference
from modules.pdf_generator import PDF, create_download_link

st.set_page_config(page_title="AS AUTO", page_icon="🚗", layout="wide")
st.title("🚗 AS AUTO :red[DEVIS] et :blue[FACTURE]")

st.sidebar.image("images/as_auto.png", width=200)

type_document = st.sidebar.selectbox(
    "Choisir le type de document voulu.", ("Devis", "Facture"), key="type_document"
)

date = st.sidebar.date_input("Date du document :", format="DD/MM/YYYY")


st.sidebar.title("Informations Client:")


nom = st.sidebar.text_input("Nom:", key="nom")
prenom = st.sidebar.text_input("Prénom:", key="prenom")
telephone = st.sidebar.text_input("Tél:", key="telephone")
email = st.sidebar.text_input("Email:", key="email")
adresse = st.sidebar.text_input("Adresse postale:", key="adresse")

col_voit, col_vide, col_prest = st.columns(spec=[0.1, 0.01, 0.89])

with col_voit:
    st.title("Info voiture:")
    marque = st.text_input("Marque", key="marque")
    modele = st.text_input("Modèle", key="modele")
    immatriculation = st.text_input("Immatriculation", key="immatriculation")
    nserie = st.text_input("Numéro de série", key="nserie")
    kilometrage = st.number_input(
        "Kilométrage",
        min_value=0,
        max_value=1500000,
        step=10000,
        value=None,
        key="kilometrage",
    )

with col_prest:
    st.title("Prestations effectué")

    with st.container():
        data_init = pd.DataFrame(
            {
                "type_prestation": ["None"],
                "quantite": [None],
                "prix": [None],
                "total_prest": [None],
            }
        )
        config = {
            "type_prestation": st.column_config.TextColumn("Prestation"),
            "quantite": st.column_config.NumberColumn(
                "Quantité", width="small", default=1, min_value=0
            ),
            "prix": st.column_config.NumberColumn(
                "Prix", min_value=0, max_value=100000
            ),
            "total_prest": st.column_config.NumberColumn(
                "Total", min_value=0, max_value=100000
            ),
        }
        df = st.data_editor(
            data_init[1:],
            column_config=config,
            num_rows="dynamic",
            use_container_width=True,
            key="data_edit",
        )
        st.session_state["prestations"] = df
        data = st.session_state["prestations"]

    gen_doc = st.button("Générer document")
    if gen_doc:
        st.session_state["montant_total_output"] = num2words(
            float(df["total_prest"].sum()), to="currency", lang="fr"
        )
        st.session_state["ref"] = get_reference(st.session_state)

        pdf = PDF(st.session_state)
        pdf.add_page()

        html = create_download_link(
            pdf.output(dest="S").encode("latin-1"), st.session_state["ref"]
        )
        st.markdown(html, unsafe_allow_html=True)
