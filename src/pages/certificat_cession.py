import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from src.modules.cession_data import CLE, from_session_state
from src.modules.cession_pdf import remplir_cerfa
from src.modules.reference import get_reference_cession
from src.modules.vendeur_profiles import AUCUN, appliquer_profil, lister_profils

PERSONNE_PHYSIQUE = "Personne physique ou entreprise individuelle"
PERSONNE_MORALE = "Personne morale"
TYPES_PERSONNE = [PERSONNE_PHYSIQUE, PERSONNE_MORALE]

# Codes de la rubrique J.1 d'une carte grise ; la liste reste ouverte à la saisie.
GENRES = [
    "VP", "CTTE", "CAM", "VASP", "TRR", "REM", "RESP",
    "MTL", "MTT1", "MTT2", "CL", "CM", "QM", "TCP", "TM",
]
TYPES_VOIE = [
    "", "RUE", "AVENUE", "BOULEVARD", "ALLEE", "CHEMIN", "IMPASSE",
    "PLACE", "ROUTE", "SENTIER", "SQUARE", "QUAI", "LIEU-DIT",
]


SAISIE_DATE = "JJ/MM/AAAA — les « / » sont ajoutés tout seuls : tapez 05092014."
SAISIE_HEURE = "HH:MM — les « : » sont ajoutés tout seuls : tapez 1430."


def _decouper_date(brut: str) -> tuple[str, str, str] | None:
    """Découpe une date saisie librement en (jour, mois, année) sur 2/2/4 chiffres.

    Accepte « 05092014 », « 5/9/2014 », « 05-09-14 », « 5.9.14 »...
    Renvoie None si la saisie n'est pas exploitable.
    """
    morceaux = [m for m in re.split(r"\D+", brut) if m]
    if len(morceaux) == 3:
        jour, mois, annee = morceaux
    else:
        chiffres = re.sub(r"\D", "", brut)
        if len(chiffres) not in (6, 8):  # JJMMAA ou JJMMAAAA
            return None
        jour, mois, annee = chiffres[:2], chiffres[2:4], chiffres[4:]

    if len(annee) == 2:
        # Un véhicule ne s'immatricule pas dans le futur : 40 sépare 20xx de 19xx.
        annee = ("20" if int(annee) <= 40 else "19") + annee
    return jour.zfill(2), mois.zfill(2), annee


def _normaliser_date(cle: str) -> None:
    """Callback des champs date : remet la saisie au format JJ/MM/AAAA.

    Une saisie inexploitable est laissée telle quelle, pour ne pas effacer ce que
    l'utilisateur vient de taper.
    """
    brut = str(st.session_state.get(cle, "")).strip()
    if not brut:
        return
    decoupe = _decouper_date(brut)
    if decoupe is None:
        return
    jour, mois, annee = decoupe
    try:
        date(int(annee), int(mois), int(jour))
    except ValueError:
        return
    st.session_state[cle] = f"{jour}/{mois}/{annee}"


def _normaliser_heure(cle: str) -> None:
    """Callback du champ heure : « 1430 », « 14h30 », « 14 30 » -> « 14:30 »."""
    brut = str(st.session_state.get(cle, "")).strip()
    if not brut:
        return
    chiffres = re.sub(r"\D", "", brut)
    if len(chiffres) == 4:
        heure, minute = chiffres[:2], chiffres[2:]
    elif len(chiffres) in (1, 2):
        heure, minute = chiffres.zfill(2), "00"
    else:
        return
    if int(heure) > 23 or int(minute) > 59:
        return
    st.session_state[cle] = f"{heure}:{minute}"


CHAMPS_DATE = {
    "date_1re_immat": "Date de 1re immatriculation",
    "date_certificat": "Date du certificat d'immatriculation",
    "date_cession": "Date de cession",
    "nouv_naissance_date": "Né(e) le (nouveau propriétaire)",
}


def _saisies_illisibles() -> list[str]:
    """Champs date/heure remplis mais que le formulaire ne saura pas imprimer.

    Une saisie ambiguë comme « 1082026 » n'est volontairement pas devinée : mieux
    vaut prévenir que d'écrire une date fausse sur un document officiel.
    """
    illisibles = []
    for cle, libelle in CHAMPS_DATE.items():
        brut = str(st.session_state.get(f"{CLE}{cle}", "")).strip()
        if not brut:
            continue
        morceaux = brut.split("/")
        try:
            if len(morceaux) != 3:
                raise ValueError(brut)
            jour, mois, annee = morceaux
            date(int(annee), int(mois), int(jour))
        except ValueError:
            illisibles.append(f"{libelle} : « {brut} »")

    heure = str(st.session_state.get(f"{CLE}heure_cession", "")).strip()
    if heure and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", heure):
        illisibles.append(f"Heure de cession : « {heure} »")
    return illisibles


def _maintenant_paris() -> None:
    """Callback du bouton : remplit date et heure de cession en une seule action.

    L'heure de Paris est calculée explicitement car le serveur peut tourner en UTC.
    """
    maintenant = datetime.now(ZoneInfo("Europe/Paris"))
    st.session_state[f"{CLE}date_cession"] = maintenant.strftime("%d/%m/%Y")
    st.session_state[f"{CLE}heure_cession"] = maintenant.strftime("%H:%M")


# Valeur initiale posée dans l'état plutôt que via `value=` : le champ est aussi
# alimenté par les profils vendeurs, et Streamlit refuse de combiner les deux.
# La valeur vient des secrets, pour ne pas figer une commune dans le dépôt.
st.session_state.setdefault(f"{CLE}ville", str(st.secrets.get("ville_par_defaut", "")))

st.title("📄 Certificat de cession d'un véhicule")
st.caption(
    "CERFA 15776*02 — le document généré est le formulaire officiel pré-rempli, "
    "à imprimer puis à dater et signer à la main."
)

# --- Aide au calage (barre latérale) ---------------------------------------
with st.sidebar.expander("🛠️ Mode calage"):
    st.caption(
        "À n'utiliser que si le texte ne tombe pas en face des cases à l'impression."
    )
    calage = st.checkbox("Afficher la grille de repérage", key=f"{CLE}calage")
    decalage_x = st.number_input(
        "Décalage horizontal (pt)", -30.0, 30.0, 0.0, 0.5, key=f"{CLE}dx"
    )
    decalage_y = st.number_input(
        "Décalage vertical (pt)", -30.0, 30.0, 0.0, 0.5, key=f"{CLE}dy"
    )

# ---------------------------------------------------------------------------
# ① Le véhicule
# ---------------------------------------------------------------------------
st.subheader("① Le véhicule")
st.caption("Tous les champs sont facultatifs : ce qui est laissé vide reste vierge.")

col_a, col_e, col_b = st.columns([0.3, 0.4, 0.3])
col_a.text_input(
    "Immatriculation",
    key=f"{CLE}immatriculation",
    placeholder="AB-123-CD",
    help="Rubrique **A** — 9 cases sur le formulaire.",
)
col_e.text_input(
    "N° d'identification (VIN)",
    key=f"{CLE}identification",
    placeholder="VF1ABCDEF12345678",
    help="Rubrique **E** — 17 caractères.",
)
col_b.text_input(
    "Date de 1re immatriculation",
    key=f"{CLE}date_1re_immat",
    placeholder="JJ/MM/AAAA",
    on_change=_normaliser_date,
    args=(f"{CLE}date_1re_immat",),
    help=f"Rubrique **B**. {SAISIE_DATE}",
)

col_d1, col_d2, col_j1, col_d3 = st.columns(4)
col_d1.text_input("Marque", key=f"{CLE}marque", placeholder="RENAULT", help="Rubrique **D.1**.")
col_d2.text_input(
    "Type, variante, version",
    key=f"{CLE}type_variante",
    placeholder="MEGANE III",
    help="Rubrique **D.2**.",
)
col_j1.selectbox(
    "Genre national",
    GENRES,
    index=None,
    accept_new_options=True,
    key=f"{CLE}genre",
    placeholder="VP",
    help="Rubrique **J.1** — vous pouvez saisir un code absent de la liste.",
)
col_d3.text_input(
    "Dénomination commerciale",
    key=f"{CLE}denomination",
    placeholder="MEGANE",
    help="Rubrique **D.3**.",
)

col_km, col_cert = st.columns([0.3, 0.7])
col_km.text_input(
    "Kilométrage au compteur", key=f"{CLE}kilometrage", placeholder="123456"
)
certificat = col_cert.radio(
    "Présence du certificat d'immatriculation",
    ["OUI", "NON"],
    horizontal=True,
    key=f"{CLE}certificat",
)

if certificat == "OUI":
    col_formule, col_date_cert = st.columns(2)
    col_formule.text_input(
        "Numéro de formule",
        key=f"{CLE}numero_formule",
        placeholder="2014AB12345",
        help="Figure sur le 1er volet du certificat d'immatriculation (format AB-123-CD).",
    )
    col_date_cert.text_input(
        "ou (I) date du certificat d'immatriculation",
        key=f"{CLE}date_certificat",
        placeholder="JJ/MM/AAAA",
        on_change=_normaliser_date,
        args=(f"{CLE}date_certificat",),
        help="Uniquement pour un ancien format d'immatriculation (type 123 AB 45). "
        f"{SAISIE_DATE}",
    )
else:
    st.text_input(
        "Motif d'absence de certificat d'immatriculation", key=f"{CLE}motif_absence"
    )

# ---------------------------------------------------------------------------
# ② L'ancien propriétaire
# ---------------------------------------------------------------------------
st.subheader("② L'ancien propriétaire")

profils = lister_profils(st.secrets)
if profils:
    st.selectbox(
        "Profil pré-enregistré",
        [AUCUN, *profils],
        format_func=lambda cle: profils.get(cle, cle),
        key=f"{CLE}profil",
        on_change=appliquer_profil,
        help="Les profils sont définis dans `.streamlit/secrets.toml`, section `vendeur_profiles`.",
    )
else:
    st.caption(
        "Aucun profil vendeur : ajoutez une section `[vendeur_profiles.<nom>]` dans "
        "`.streamlit/secrets.toml` pour pré-remplir ce bloc en un clic."
    )

col_type, col_sexe = st.columns([0.7, 0.3])
type_ancien = col_type.radio(
    "Type de personne", TYPES_PERSONNE, key=f"{CLE}anc_type_personne"
)
sans_cocher_ancien = col_type.checkbox(
    "Ne pas cocher ces cases sur le formulaire",
    key=f"{CLE}anc_sans_cocher",
    help="Laisse les cases « personne physique / morale » et « sexe » vierges, "
    "à cocher à la main ou à recouvrir d'un cachet. Le choix ci-dessus sert "
    "quand même à savoir quels champs d'identité remplir.",
)
col_sexe.radio(
    "Sexe",
    ["M", "F"],
    horizontal=True,
    key=f"{CLE}anc_sexe",
    disabled=type_ancien == PERSONNE_MORALE or sans_cocher_ancien,
    help="Sans objet pour une personne morale.",
)

if type_ancien == PERSONNE_MORALE:
    col_rs, col_siret = st.columns([0.7, 0.3])
    col_rs.text_input("Raison sociale", key=f"{CLE}anc_raison_sociale")
    col_siret.text_input("N° SIRET", key=f"{CLE}anc_siret", placeholder="12345678900012")
else:
    col_nom, col_usage, col_prenom, col_siret = st.columns(4)
    col_nom.text_input("Nom", key=f"{CLE}anc_nom")
    col_usage.text_input("Nom d'usage", key=f"{CLE}anc_nom_usage")
    col_prenom.text_input("Prénom", key=f"{CLE}anc_prenom")
    col_siret.text_input(
        "N° SIRET", key=f"{CLE}anc_siret", help="Le cas échéant.", placeholder="12345678900012"
    )

col_num, col_ext, col_tvoie, col_nvoie = st.columns([0.15, 0.15, 0.25, 0.45])
col_num.text_input("N° de la voie", key=f"{CLE}anc_voie_numero")
col_ext.text_input("Extension", key=f"{CLE}anc_voie_extension", placeholder="BIS, TER…")
col_tvoie.selectbox(
    "Type de voie", TYPES_VOIE, accept_new_options=True, key=f"{CLE}anc_voie_type"
)
col_nvoie.text_input("Nom de la voie", key=f"{CLE}anc_voie_nom")

col_cp, col_commune = st.columns([0.25, 0.75])
col_cp.text_input("Code postal", key=f"{CLE}anc_code_postal", placeholder="00000")
col_commune.text_input("Commune", key=f"{CLE}anc_commune")

# ---------------------------------------------------------------------------
# La cession
# ---------------------------------------------------------------------------
st.subheader("La cession")

st.radio(
    "Le véhicule est cédé",
    ["Céder", "Céder pour destruction"],
    horizontal=True,
    key=f"{CLE}motif_cession",
)

col_date, col_heure, col_bouton = st.columns([0.3, 0.2, 0.5])
col_date.text_input(
    "Date de cession",
    key=f"{CLE}date_cession",
    placeholder="JJ/MM/AAAA",
    on_change=_normaliser_date,
    args=(f"{CLE}date_cession",),
    help=SAISIE_DATE,
)
col_heure.text_input(
    "Heure de cession",
    key=f"{CLE}heure_cession",
    placeholder="HH:MM",
    on_change=_normaliser_heure,
    args=(f"{CLE}heure_cession",),
    help=SAISIE_HEURE,
)
col_bouton.write("")
col_bouton.button(
    "🕒 Maintenant (heure de Paris)",
    on_click=_maintenant_paris,
    help="Remplit la date et l'heure de cession en une seule action.",
)

st.markdown("**Je certifie en outre :**")
st.checkbox(
    "Avoir remis au nouveau propriétaire un certificat de situation administrative "
    "de moins de quinze jours",
    value=True,
    key=f"{CLE}certifie_situation",
)
st.checkbox(
    "Que ce véhicule n'a pas subi de transformation notable",
    value=True,
    key=f"{CLE}certifie_transformation",
)
certifie_vhu = st.checkbox(
    "Que ce véhicule est cédé pour destruction à un professionnel VHU",
    key=f"{CLE}certifie_vhu",
)
if certifie_vhu:
    st.text_input(
        "N° d'agrément VHU du professionnel acquéreur",
        key=f"{CLE}agrement_vhu",
        help="Obligatoire pour une voiture particulière, une camionnette ou un "
        "cyclomoteur à trois roues.",
    )

# ---------------------------------------------------------------------------
# ③ Le nouveau propriétaire (facultatif)
# ---------------------------------------------------------------------------
with st.expander("③ Le nouveau propriétaire (facultatif)"):
    st.caption(
        "Laissé vide, ce bloc reste vierge sur le formulaire : l'acquéreur le remplit "
        "à la main au moment de la vente."
    )

    col_type_n, col_sexe_n = st.columns([0.7, 0.3])
    type_nouveau = col_type_n.radio(
        "Type de personne", TYPES_PERSONNE, key=f"{CLE}nouv_type_personne"
    )
    sans_cocher_nouveau = col_type_n.checkbox(
        "Ne pas cocher ces cases sur le formulaire",
        key=f"{CLE}nouv_sans_cocher",
        help="Laisse les cases « personne physique / morale » et « sexe » vierges.",
    )
    col_sexe_n.radio(
        "Sexe",
        ["M", "F"],
        horizontal=True,
        key=f"{CLE}nouv_sexe",
        disabled=type_nouveau == PERSONNE_MORALE or sans_cocher_nouveau,
    )

    if type_nouveau == PERSONNE_MORALE:
        col_rs_n, col_siret_n = st.columns([0.7, 0.3])
        col_rs_n.text_input("Raison sociale", key=f"{CLE}nouv_raison_sociale")
        col_siret_n.text_input("N° SIRET", key=f"{CLE}nouv_siret")
    else:
        col_nom_n, col_usage_n, col_prenom_n, col_siret_n = st.columns(4)
        col_nom_n.text_input("Nom", key=f"{CLE}nouv_nom")
        col_usage_n.text_input("Nom d'usage", key=f"{CLE}nouv_nom_usage")
        col_prenom_n.text_input("Prénom", key=f"{CLE}nouv_prenom")
        col_siret_n.text_input("N° SIRET", key=f"{CLE}nouv_siret")

    col_naiss, col_lieu = st.columns([0.3, 0.7])
    col_naiss.text_input(
        "Né(e) le",
        key=f"{CLE}nouv_naissance_date",
        placeholder="JJ/MM/AAAA",
        on_change=_normaliser_date,
        args=(f"{CLE}nouv_naissance_date",),
        help=SAISIE_DATE,
    )
    col_lieu.text_input("à", key=f"{CLE}nouv_naissance_lieu")

    col_num_n, col_ext_n, col_tvoie_n, col_nvoie_n = st.columns([0.15, 0.15, 0.25, 0.45])
    col_num_n.text_input("N° de la voie", key=f"{CLE}nouv_voie_numero")
    col_ext_n.text_input("Extension", key=f"{CLE}nouv_voie_extension")
    col_tvoie_n.selectbox(
        "Type de voie", TYPES_VOIE, accept_new_options=True, key=f"{CLE}nouv_voie_type"
    )
    col_nvoie_n.text_input("Nom de la voie", key=f"{CLE}nouv_voie_nom")

    col_cp_n, col_commune_n = st.columns([0.25, 0.75])
    col_cp_n.text_input("Code postal", key=f"{CLE}nouv_code_postal")
    col_commune_n.text_input("Commune", key=f"{CLE}nouv_commune")

    st.checkbox(
        "Cocher les deux déclarations de l'acquéreur "
        "(acquisition du véhicule et information sur sa situation administrative)",
        key=f"{CLE}nouveau_certifie",
    )

# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------
st.subheader("Signature")

col_ville, col_date_sig, col_opposition = st.columns([0.3, 0.3, 0.4])
col_ville.text_input("Fait à", key=f"{CLE}ville")
col_date_sig.date_input(
    "Le",
    value=None,
    format="DD/MM/YYYY",
    key=f"{CLE}date_signature",
    help="Laissée vide, la ligne « le … » reste vierge sur le formulaire.",
)
col_opposition.write("")
col_opposition.checkbox(
    "M'opposer à la réutilisation de mes données personnelles à des fins de "
    "prospection commerciale",
    key=f"{CLE}opposition",
)

# ---------------------------------------------------------------------------
# Génération
# ---------------------------------------------------------------------------
if st.button("Générer le certificat de cession", type="primary"):
    donnees = from_session_state(st.session_state)
    try:
        st.session_state[f"{CLE}pdf"] = remplir_cerfa(
            donnees, calage=calage, decalage=(decalage_x, decalage_y)
        )
        # La date de signature peut rester vide : le nom du fichier se rabat
        # alors sur la date du jour.
        date_document = st.session_state[f"{CLE}date_signature"] or datetime.now(
            ZoneInfo("Europe/Paris")
        ).date()
        st.session_state[f"{CLE}ref"] = get_reference_cession(
            donnees.immatriculation, date_document
        )
    except Exception as erreur:
        st.session_state.pop(f"{CLE}pdf", None)
        st.error(
            f"Erreur lors de la génération du certificat de cession.\n\n{erreur}",
            icon="🚨",
        )

if st.session_state.get(f"{CLE}pdf"):
    illisibles = _saisies_illisibles()
    if illisibles:
        st.warning(
            "Ces saisies n'ont pas pu être interprétées et resteront **vides** sur "
            "le formulaire. Corrigez-les puis regénérez :\n\n"
            + "\n".join(f"- {ligne}" for ligne in illisibles),
            icon="⚠️",
        )
    st.success("Certificat généré : les deux exemplaires sont dans le même fichier.")
    st.download_button(
        "⬇️ Télécharger le certificat de cession",
        data=st.session_state[f"{CLE}pdf"],
        file_name=f"{st.session_state[f'{CLE}ref']}.pdf",
        mime="application/pdf",
    )
