"""Profils vendeurs pré-enregistrés dans `.streamlit/secrets.toml`.

Schéma attendu (tables imbriquées TOML) :

    [vendeur_profiles.mon_profil]
    label         = "Libellé affiché dans la liste"
    type_personne = "physique"   # ou "morale"
    sexe          = "M"
    nom           = "DUPONT"
    ...
"""

import streamlit as st

from src.modules.cession_data import CLE

AUCUN = "— aucun —"

# Clé du profil TOML -> clé du widget (sans le préfixe `cess_`).
_MAPPAGE = {
    "type_personne": "anc_type_personne",
    "sexe": "anc_sexe",
    "nom": "anc_nom",
    "nom_usage": "anc_nom_usage",
    "prenom": "anc_prenom",
    "raison_sociale": "anc_raison_sociale",
    "siret": "anc_siret",
    "voie_numero": "anc_voie_numero",
    "voie_extension": "anc_voie_extension",
    "voie_type": "anc_voie_type",
    "voie_nom": "anc_voie_nom",
    "code_postal": "anc_code_postal",
    "commune": "anc_commune",
    "fait_a": "ville",
}

# Les radios stockent le libellé affiché, pas la valeur brute du TOML.
_LIBELLES_PERSONNE = {
    "physique": "Personne physique ou entreprise individuelle",
    "morale": "Personne morale",
}


def lister_profils(secrets) -> dict[str, str]:
    """{identifiant: libellé}. Dictionnaire vide si la section est absente."""
    if "vendeur_profiles" not in secrets:
        return {}
    profils = secrets["vendeur_profiles"]
    return {
        identifiant: profils[identifiant].get("label", identifiant)
        for identifiant in profils
    }


def charger_profil(secrets, identifiant: str) -> dict:
    return dict(secrets["vendeur_profiles"][identifiant])


def appliquer_profil() -> None:
    """Callback `on_change` du sélecteur de profil.

    Un callback s'exécute **avant** le rerun, donc avant l'instanciation des widgets
    ciblés : y écrire dans `session_state` est légal, contrairement à une écriture
    faite dans le corps d'un `if st.button(...)`.
    """
    choix = st.session_state.get(f"{CLE}profil")
    if not choix or choix == AUCUN:
        return

    profil = charger_profil(st.secrets, choix)
    for cle_profil, cle_widget in _MAPPAGE.items():
        if cle_profil not in profil:
            continue  # un profil partiel n'écrase pas la saisie manuelle
        valeur = profil[cle_profil]
        if cle_profil == "type_personne":
            valeur = _LIBELLES_PERSONNE.get(str(valeur).lower(), valeur)
        st.session_state[f"{CLE}{cle_widget}"] = str(valeur)
