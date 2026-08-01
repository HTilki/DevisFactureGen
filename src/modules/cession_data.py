"""Données saisies pour un certificat de cession, indépendantes de Streamlit.

Découpler le formulaire du générateur permet de régénérer un PDF depuis un simple
`python -c` pendant le calage des coordonnées, sans lancer l'application.
"""

from dataclasses import dataclass, field, fields
from datetime import date

CLE = "cess_"  # préfixe de toutes les clés de widget de la page cession


@dataclass
class Proprietaire:
    """Un des deux blocs identité du CERFA (ancien ou nouveau propriétaire)."""

    type_personne: str = "physique"  # "physique" | "morale"
    sexe: str = "M"  # "M" | "F"
    # Faux quand les cases type de personne / sexe doivent rester vierges,
    # pour être cochées à la main ou couvertes par un cachet.
    cocher_type: bool = True
    nom: str = ""
    nom_usage: str = ""
    prenom: str = ""
    raison_sociale: str = ""
    siret: str = ""
    voie_numero: str = ""
    voie_extension: str = ""
    voie_type: str = ""
    voie_nom: str = ""
    code_postal: str = ""
    commune: str = ""
    naissance_date: str = ""  # JJ/MM/AAAA, bloc « nouveau propriétaire » uniquement
    naissance_lieu: str = ""

    @property
    def identite(self) -> str:
        """Le CERFA n'offre qu'une seule ligne pour NOM, NOM D'USAGE et PRÉNOM
        ou la RAISON SOCIALE : on la compose ici."""
        if self.type_personne == "morale":
            return self.raison_sociale
        morceaux = [self.nom]
        if self.nom_usage:
            morceaux.append(f"({self.nom_usage})")
        if self.prenom:
            morceaux.append(self.prenom)
        return " ".join(m for m in morceaux if m)

    @property
    def est_rempli(self) -> bool:
        """Vrai dès qu'au moins un champ du bloc est renseigné."""
        return any(
            getattr(self, f.name)
            for f in fields(self)
            if f.name not in ("type_personne", "sexe", "cocher_type")
        )


@dataclass
class CessionData:
    # ① Le véhicule
    immatriculation: str = ""
    identification: str = ""  # (E) VIN
    date_1re_immat: str = ""  # JJ/MM/AAAA
    marque: str = ""  # D.1
    type_variante: str = ""  # D.2
    genre: str = ""  # J.1
    denomination: str = ""  # D.3
    kilometrage: str = ""
    certificat_present: bool = True
    numero_formule: str = ""
    date_certificat: str = ""  # (I), ancien format d'immatriculation
    motif_absence: str = ""

    # ② Ancien propriétaire
    ancien: Proprietaire = field(default_factory=Proprietaire)

    # Cession
    pour_destruction: bool = False
    date_cession: str = ""  # JJ/MM/AAAA
    heure_cession: str = ""  # HH:MM
    certifie_situation: bool = True
    certifie_transformation: bool = True
    certifie_vhu: bool = False
    agrement_vhu: str = ""

    # ③ Nouveau propriétaire (facultatif, vide par défaut)
    nouveau: Proprietaire = field(default_factory=Proprietaire)
    nouveau_certifie: bool = False

    # Signature
    # La ville par défaut vient des secrets (clé `ville_par_defaut`), pas du code.
    ville: str = ""
    date_signature: str = ""  # JJ/MM/AAAA
    opposition_prospection: bool = False

    @classmethod
    def exemple(cls) -> "CessionData":
        """Jeu de données de calage : chaque champ porte un marqueur reconnaissable
        et occupe toute la place disponible, pour rendre les débordements évidents."""
        ancien = Proprietaire(
            nom="DUPONT",
            prenom="JEAN-BAPTISTE",
            siret="12345678900012",
            voie_numero="123",
            voie_extension="BIS",
            voie_type="AVENUE",
            voie_nom="DU GENERAL DE GAULLE",
            code_postal="00000",
            commune="VILLENEUVE-SUR-EXEMPLE",
        )
        nouveau = Proprietaire(
            type_personne="morale",
            raison_sociale="GARAGE DES DEUX PONTS SARL",
            siret="98765432100019",
            voie_numero="7",
            voie_type="RUE",
            voie_nom="DE LA REPUBLIQUE",
            code_postal="11111",
            commune="SAINT-EXEMPLE",
            naissance_date="02/03/1980",
            naissance_lieu="PARIS 15E ARRONDISSEMENT",
        )
        return cls(
            immatriculation="AB-123-CD",
            identification="VF1ABCDEF12345678",
            date_1re_immat="05/09/2014",
            marque="RENAULT",
            type_variante="MEGANE III",
            genre="VP",
            denomination="MEGANE",
            kilometrage="123456",
            numero_formule="2014AB12345",
            ancien=ancien,
            date_cession="01/08/2026",
            heure_cession="14:30",
            nouveau=nouveau,
            date_signature="01/08/2026",
        )


def _txt(session_state, cle: str, defaut: str = "") -> str:
    valeur = session_state.get(f"{CLE}{cle}", defaut)
    return "" if valeur is None else str(valeur)


def _bool(session_state, cle: str, defaut: bool = False) -> bool:
    return bool(session_state.get(f"{CLE}{cle}", defaut))


def _date(session_state, cle: str) -> str:
    valeur = session_state.get(f"{CLE}{cle}")
    if isinstance(valeur, date):
        return valeur.strftime("%d/%m/%Y")
    return "" if valeur is None else str(valeur)


def _type_personne(session_state, prefixe: str) -> str:
    """Les radios stockent le libellé complet du CERFA : on le ramène à physique/morale."""
    valeur = _txt(session_state, f"{prefixe}_type_personne", "physique").lower()
    return "morale" if "morale" in valeur else "physique"


def _proprietaire(session_state, prefixe: str) -> Proprietaire:
    return Proprietaire(
        type_personne=_type_personne(session_state, prefixe),
        sexe=_txt(session_state, f"{prefixe}_sexe", "M"),
        cocher_type=not _bool(session_state, f"{prefixe}_sans_cocher"),
        nom=_txt(session_state, f"{prefixe}_nom"),
        nom_usage=_txt(session_state, f"{prefixe}_nom_usage"),
        prenom=_txt(session_state, f"{prefixe}_prenom"),
        raison_sociale=_txt(session_state, f"{prefixe}_raison_sociale"),
        # Les peignes SIRET et code postal n'ont qu'une case par chiffre : on retire
        # les espaces de mise en forme (« 123 456 789 00012 »).
        siret=_txt(session_state, f"{prefixe}_siret").replace(" ", ""),
        voie_numero=_txt(session_state, f"{prefixe}_voie_numero"),
        voie_extension=_txt(session_state, f"{prefixe}_voie_extension"),
        voie_type=_txt(session_state, f"{prefixe}_voie_type"),
        voie_nom=_txt(session_state, f"{prefixe}_voie_nom"),
        commune=_txt(session_state, f"{prefixe}_commune"),
        code_postal=_txt(session_state, f"{prefixe}_code_postal").replace(" ", ""),
        naissance_date=_txt(session_state, f"{prefixe}_naissance_date"),
        naissance_lieu=_txt(session_state, f"{prefixe}_naissance_lieu"),
    )


def from_session_state(session_state) -> CessionData:
    """Construit les données à partir des widgets de la page (tous préfixés `cess_`)."""
    return CessionData(
        immatriculation=_txt(session_state, "immatriculation"),
        identification=_txt(session_state, "identification"),
        date_1re_immat=_txt(session_state, "date_1re_immat"),
        marque=_txt(session_state, "marque"),
        type_variante=_txt(session_state, "type_variante"),
        genre=_txt(session_state, "genre"),
        denomination=_txt(session_state, "denomination"),
        kilometrage=_txt(session_state, "kilometrage"),
        certificat_present=_txt(session_state, "certificat", "OUI") == "OUI",
        numero_formule=_txt(session_state, "numero_formule"),
        date_certificat=_txt(session_state, "date_certificat"),
        motif_absence=_txt(session_state, "motif_absence"),
        ancien=_proprietaire(session_state, "anc"),
        pour_destruction=_txt(session_state, "motif_cession", "Céder")
        == "Céder pour destruction",
        date_cession=_txt(session_state, "date_cession"),
        heure_cession=_txt(session_state, "heure_cession"),
        certifie_situation=_bool(session_state, "certifie_situation", True),
        certifie_transformation=_bool(session_state, "certifie_transformation", True),
        certifie_vhu=_bool(session_state, "certifie_vhu"),
        agrement_vhu=_txt(session_state, "agrement_vhu"),
        nouveau=_proprietaire(session_state, "nouv"),
        nouveau_certifie=_bool(session_state, "nouveau_certifie"),
        ville=_txt(session_state, "ville"),
        date_signature=_date(session_state, "date_signature"),
        opposition_prospection=_bool(session_state, "opposition"),
    )
