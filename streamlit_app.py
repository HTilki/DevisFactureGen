import hmac
import pandas as pd
import streamlit as st
from num2words import num2words

from src.modules.app_func import get_reference
from src.modules.pdf_generator import PDF, create_download_link


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Mot de passe",
        type="password",
        on_change=password_entered,
        key="password",
        placeholder="Veuillez insérer le mot de passe pour accéder à l'application.",
    )
    if "password_correct" in st.session_state:
        st.error("😕 Mot de passe incorrect")
    return False


if not check_password():
    st.stop()

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
        try:
            st.session_state["montant_total_output"] = str(
                str(round(df["total_prest"].sum(), 2))
                +" euros ("
                + str(num2words(round(df["total_prest"].sum(), 2), to="currency", lang="fr"))
                + ")"
            )
            st.session_state["ref"] = get_reference(st.session_state)

            pdf = PDF(st.session_state)
            pdf.add_page()

            html = create_download_link(
                pdf.output(dest="S").encode("latin-1"), st.session_state["ref"]
            )
            st.markdown(html, unsafe_allow_html=True)
        except Exception as e: 
            st.error(
                f"""
                Erreur lors de la génération du fichier, vérifiez bien que toutes les cellules sont renseignés. 
                Il ne pas y avoir des lignes en trop et vide. 

                {e}""", 
                icon="🚨")
