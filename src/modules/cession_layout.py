"""Géométrie du CERFA 15776*02 (déclaration de cession d'un véhicule d'occasion).

Toutes les coordonnées sont exprimées dans le repère natif du PDF : en **points**,
origine en **bas à gauche** de la page A4.

Elles ne sont pas mesurées à l'œil : elles ont été extraites du flux de contenu du
formulaire. Les cases de saisie y sont dessinées comme des soulignements vectoriels,
donc `y` est le trait sous le champ et `largeur` sa largeur réelle. Les champs en
peigne (immatriculation, VIN, dates, code postal, SIRET...) donnent le nombre exact
de cases et leur pas.

C'est le seul fichier à retoucher pour caler le rendu.
"""

from typing import NamedTuple

# --- Page ------------------------------------------------------------------
A4_L_PT = 595.276
A4_H_PT = 841.89

# --- Réglages de rendu -----------------------------------------------------
TAILLE_TEXTE = 9.0  # taille de police par défaut
MONTEE = 2.2  # de combien la ligne de base est au-dessus du trait du CERFA
MARGE_LIGNE = 2.0  # retrait à gauche dans un champ « ligne »
TAILLE_MIN = 5.0  # en dessous, on n'essaie plus de réduire pour faire tenir

# Décalage de la croix par rapport à l'origine du glyphe « case à cocher ».
CROIX_DX = 1.0
CROIX_DY = 0.8
TAILLE_CROIX = 8.0


def y_fpdf(y_pdf: float) -> float:
    """Convertit un `y` du repère PDF (bas-gauche) vers le repère fpdf (haut-gauche)."""
    return A4_H_PT - y_pdf


class Champ(NamedTuple):
    """Un champ de saisie du formulaire.

    - `cases` > 0 : champ en peigne, un caractère centré par case, pas de `pas`.
    - `cases` == 0 : champ « ligne », texte aligné à gauche, réduit si besoin
      pour tenir dans `largeur`.
    """

    x: float
    y: float
    largeur: float = 0.0
    cases: int = 0
    pas: float = 0.0
    taille: float = TAILLE_TEXTE
    majuscules: bool = True
    saute_cases: int = 0  # cases de tête déjà pré-imprimées sur le CERFA


class Case(NamedTuple):
    """Une case à cocher (dessinée en vectoriel sur le CERFA : on écrit un X dessus)."""

    x: float
    y: float


# ---------------------------------------------------------------------------
# ① Le véhicule
# ---------------------------------------------------------------------------
VEHICULE = {
    # y=720.2 : peignes des identifiants
    "immatriculation": Champ(x=35.5, y=720.2, cases=9, pas=14.4),
    "identification": Champ(x=173.5, y=720.2, cases=17, pas=14.4, taille=8.0),
    "immat1_jour": Champ(x=440.5, y=720.2, cases=2, pas=11.6, taille=8.0),
    "immat1_mois": Champ(x=466.2, y=720.2, cases=2, pas=11.6, taille=8.0),
    "immat1_annee": Champ(x=491.9, y=720.2, cases=4, pas=11.6, taille=8.0),
    # y=696.2 : les quatre champs D.1 / D.2 / J.1 / D.3
    "marque": Champ(x=35.5, y=696.2, largeur=130.9),
    "type_variante": Champ(x=174.5, y=696.2, largeur=133.7, taille=8.0),
    "genre": Champ(x=321.5, y=696.2, largeur=111.1),
    "denomination": Champ(x=441.5, y=696.2, largeur=116.7),
    # Kilométrage compteur
    "kilometrage": Champ(x=206.2, y=671.3, largeur=66.9),
    # Certificat d'immatriculation présent : n° de formule.
    # Les deux premières cases portent déjà « 2 0 » pré-imprimé sur le CERFA.
    "formule": Champ(x=142.1, y=642.0, cases=11, pas=14.4, saute_cases=2),
    # ... ou (I) date du certificat d'immatriculation (ancien format)
    "date_cert_jour": Champ(x=222.3, y=620.4, cases=2, pas=11.6, taille=8.0),
    "date_cert_mois": Champ(x=247.9, y=620.4, cases=2, pas=11.6, taille=8.0),
    "date_cert_annee": Champ(x=273.6, y=620.4, cases=4, pas=11.6, taille=8.0),
    # Motif d'absence de certificat : deux lignes en pointillés typographiques
    "motif1": Champ(x=339.0, y=632.6, largeur=250.0, taille=8.0, majuscules=False),
    "motif2": Champ(x=339.0, y=620.0, largeur=250.0, taille=8.0, majuscules=False),
}

CASES_VEHICULE = {
    "certificat_oui": Case(x=35.5, y=641.8),
    "certificat_non": Case(x=337.5, y=644.5),
}


# ---------------------------------------------------------------------------
# ② / ③ Blocs identité — mêmes x, y propres à chaque bloc
# ---------------------------------------------------------------------------
def _bloc_identite(y_identite: float, y_voie: float, y_commune: float) -> dict:
    """Construit les champs d'un bloc propriétaire : les `x` sont communs aux deux blocs."""
    return {
        # « Je soussigné(e), » : NOM, NOM D'USAGE et PRÉNOM ou RAISON SOCIALE
        "identite": Champ(x=89.6, y=y_identite, largeur=286.8),
        "siret": Champ(x=394.5, y=y_identite, cases=14, pas=11.6, taille=7.5),
        # Adresse complète
        "voie_numero": Champ(x=107.5, y=y_voie, largeur=43.0),
        "voie_extension": Champ(x=156.0, y=y_voie, largeur=43.0),
        "voie_type": Champ(x=204.6, y=y_voie, largeur=71.4, taille=8.0),
        "voie_nom": Champ(x=281.5, y=y_voie, largeur=278.3),
        "code_postal": Champ(x=107.5, y=y_commune, cases=5, pas=14.4),
        "commune": Champ(x=190.8, y=y_commune, largeur=369.0),
    }


ANCIEN = _bloc_identite(y_identite=543.3, y_voie=512.1, y_commune=492.1)

NOUVEAU = _bloc_identite(y_identite=211.4, y_voie=167.7, y_commune=147.7)
# Le bloc « nouveau propriétaire » a en plus une ligne « né(e) le … à … ».
NOUVEAU.update(
    {
        "naissance_jour": Champ(x=70.7, y=189.3, cases=2, pas=11.6, taille=8.0),
        "naissance_mois": Champ(x=96.4, y=189.3, cases=2, pas=11.6, taille=8.0),
        "naissance_annee": Champ(x=122.1, y=189.3, cases=4, pas=11.6, taille=8.0),
        "naissance_lieu": Champ(x=182.1, y=189.3, largeur=377.5),
    }
)

CASES_ANCIEN = {
    "physique": Case(x=35.5, y=573.4),
    "morale": Case(x=35.5, y=563.4),
    "sexe_m": Case(x=278.8, y=573.4),
    "sexe_f": Case(x=302.7, y=573.4),
    "ceder": Case(x=184.7, y=467.4),
    "ceder_destruction": Case(x=235.5, y=467.4),
    "certifie_situation": Case(x=35.5, y=418.1),
    "certifie_transformation": Case(x=35.5, y=398.5),
    "certifie_vhu": Case(x=35.5, y=378.9),
}

CASES_NOUVEAU = {
    "physique": Case(x=35.5, y=241.5),
    "morale": Case(x=35.5, y=231.5),
    "sexe_m": Case(x=278.8, y=241.5),
    "sexe_f": Case(x=302.7, y=241.5),
    "acquerir": Case(x=35.5, y=110.6),
    "informe": Case(x=35.5, y=97.8),
}


# ---------------------------------------------------------------------------
# Cession : « Le JJ MM AAAA à HH MM le véhicule désigné ci-dessus »
# ---------------------------------------------------------------------------
CESSION = {
    "jour": Champ(x=46.8, y=450.0, cases=2, pas=11.6, taille=8.0),
    "mois": Champ(x=72.5, y=450.0, cases=2, pas=11.6, taille=8.0),
    "annee": Champ(x=98.1, y=450.0, cases=4, pas=11.6, taille=8.0),
    "heure": Champ(x=152.9, y=450.0, cases=2, pas=11.6, taille=8.0),
    "minute": Champ(x=186.9, y=450.0, cases=2, pas=11.6, taille=8.0),
}

# N° d'agrément VHU : ligne en pointillés typographiques après
# « portant le n° d'agrément : » (police 8 pt démarrant à x=45.7).
AGREMENT_VHU = Champ(x=139.0, y=367.5, largeur=110.0, taille=8.0)

# « Fait à ______, le ______ » : soulignés typographiques, police 10 pt à x=35.5.
SIGNATURE_ANCIEN = {
    "ville": Champ(x=66.0, y=326.7, largeur=110.0),
    "date": Champ(x=195.0, y=326.7, largeur=80.0),
}
SIGNATURE_NOUVEAU = {
    "ville": Champ(x=66.0, y=72.0, largeur=110.0),
    "date": Champ(x=195.0, y=72.0, largeur=80.0),
}

# Case « Je m'oppose à la réutilisation de mes données personnelles ».
CASE_OPPOSITION = Case(x=508.5, y=13.6)
