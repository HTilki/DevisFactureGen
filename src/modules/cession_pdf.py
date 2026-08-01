"""Remplissage du CERFA 15776*02 par superposition d'un calque.

`fpdf` ne sait que créer des PDF, pas en modifier : on dessine donc le texte sur un
calque A4 vide aux coordonnées natives du formulaire, puis `pypdf` fusionne ce calque
sur les deux exemplaires du CERFA officiel.
"""

import io
from pathlib import Path

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

from src.modules.cession_data import CessionData
from src.modules.cession_layout import (
    A4_H_PT,
    A4_L_PT,
    AGREMENT_VHU,
    ANCIEN,
    CASE_OPPOSITION,
    CASES_ANCIEN,
    CASES_NOUVEAU,
    CASES_VEHICULE,
    CESSION,
    CROIX_DX,
    CROIX_DY,
    MARGE_LIGNE,
    MONTEE,
    NOUVEAU,
    SIGNATURE_ANCIEN,
    SIGNATURE_NOUVEAU,
    TAILLE_CROIX,
    TAILLE_MIN,
    VEHICULE,
    Case,
    Champ,
    y_fpdf,
)
from src.modules.texte import assainir_latin1

CHEMIN_CERFA = Path(__file__).resolve().parents[2] / "assets" / "cerfa_15776-02.pdf"


def _eclater_date(valeur: str) -> tuple[str, str, str]:
    """« 05/09/2014 » -> ('05', '09', '2014'). Tolère - et . comme séparateurs."""
    if not valeur:
        return "", "", ""
    morceaux = valeur.replace("-", "/").replace(".", "/").split("/")
    if len(morceaux) != 3:
        return "", "", ""
    jour, mois, annee = (m.strip() for m in morceaux)
    return jour.zfill(2), mois.zfill(2), annee


def _eclater_heure(valeur: str) -> tuple[str, str]:
    """« 14:30 » -> ('14', '30'). Tolère h et H comme séparateurs."""
    if not valeur:
        return "", ""
    morceaux = valeur.replace("h", ":").replace("H", ":").split(":")
    if not morceaux[0].strip():
        return "", ""
    heure = morceaux[0].strip().zfill(2)
    minute = (morceaux[1].strip() if len(morceaux) > 1 else "").zfill(2)
    return heure, minute


class OverlayCession(FPDF):
    """Calque transparent aux dimensions exactes du CERFA."""

    def __init__(self):
        # unit="pt" donne k=1 : les coordonnées du calque sont celles du CERFA.
        super().__init__(orientation="P", unit="pt", format=(A4_L_PT, A4_H_PT))
        self.set_auto_page_break(False)
        self.set_margins(0, 0, 0)
        self.set_font("Helvetica", "", 9)

    # -- primitives de dessin ------------------------------------------------
    def _ecrire(self, champ: Champ, valeur, decalage=(0.0, 0.0)) -> None:
        """Écrit une valeur dans un champ. Un champ vide ne dessine rien."""
        texte = assainir_latin1(valeur)
        if not texte:
            return
        if champ.majuscules:
            texte = texte.upper()

        dx, dy = decalage
        y = y_fpdf(champ.y + MONTEE + dy)

        if champ.cases:
            self._ecrire_peigne(champ, texte, dx, y)
        else:
            self._ecrire_ligne(champ, texte, dx, y)

    def _ecrire_peigne(self, champ: Champ, texte: str, dx: float, y: float) -> None:
        """Un caractère centré par case, en sautant les cases pré-imprimées."""
        self.set_font("Helvetica", "", champ.taille)
        disponibles = champ.cases - champ.saute_cases
        # Le n° de formule est pré-imprimé « 2 0 » : on n'écrit pas ce préfixe deux fois.
        if champ.saute_cases and texte[: champ.saute_cases].isdigit():
            texte = texte[champ.saute_cases :]
        for index, caractere in enumerate(texte[:disponibles]):
            gauche = champ.x + (champ.saute_cases + index) * champ.pas + dx
            centre = gauche + (champ.pas - self.get_string_width(caractere)) / 2
            self.text(centre, y, caractere)

    def _ecrire_ligne(self, champ: Champ, texte: str, dx: float, y: float) -> None:
        """Texte aligné à gauche, réduit progressivement pour tenir dans la largeur."""
        taille = champ.taille
        if champ.largeur:
            place = champ.largeur - 2 * MARGE_LIGNE
            self.set_font("Helvetica", "", taille)
            while self.get_string_width(texte) > place and taille > TAILLE_MIN:
                taille -= 0.25
                self.set_font("Helvetica", "", taille)
        else:
            self.set_font("Helvetica", "", taille)
        self.text(champ.x + MARGE_LIGNE + dx, y, texte)

    def _cocher(self, case: Case, decalage=(0.0, 0.0)) -> None:
        dx, dy = decalage
        self.set_font("Helvetica", "B", TAILLE_CROIX)
        self.text(case.x + CROIX_DX + dx, y_fpdf(case.y + CROIX_DY + dy), "X")

    def _ecrire_date(self, champs: dict, cles: tuple, valeur: str, decalage) -> None:
        jour, mois, annee = _eclater_date(valeur)
        for cle, part in zip(cles, (jour, mois, annee)):
            self._ecrire(champs[cle], part, decalage)

    # -- rendu du formulaire -------------------------------------------------
    def dessiner_donnees(self, donnees: CessionData, decalage=(0.0, 0.0)) -> None:
        self._dessiner_vehicule(donnees, decalage)
        self._dessiner_proprietaire(ANCIEN, CASES_ANCIEN, donnees.ancien, decalage)
        self._dessiner_cession(donnees, decalage)
        self._dessiner_nouveau(donnees, decalage)
        self._dessiner_signatures(donnees, decalage)

    def _dessiner_vehicule(self, donnees: CessionData, decalage) -> None:
        for cle, valeur in (
            ("immatriculation", donnees.immatriculation),
            ("identification", donnees.identification),
            ("marque", donnees.marque),
            ("type_variante", donnees.type_variante),
            ("genre", donnees.genre),
            ("denomination", donnees.denomination),
            ("kilometrage", donnees.kilometrage),
        ):
            self._ecrire(VEHICULE[cle], valeur, decalage)

        self._ecrire_date(
            VEHICULE,
            ("immat1_jour", "immat1_mois", "immat1_annee"),
            donnees.date_1re_immat,
            decalage,
        )

        if donnees.certificat_present:
            self._cocher(CASES_VEHICULE["certificat_oui"], decalage)
            self._ecrire(VEHICULE["formule"], donnees.numero_formule, decalage)
            self._ecrire_date(
                VEHICULE,
                ("date_cert_jour", "date_cert_mois", "date_cert_annee"),
                donnees.date_certificat,
                decalage,
            )
        else:
            self._cocher(CASES_VEHICULE["certificat_non"], decalage)
            self._ecrire(VEHICULE["motif1"], donnees.motif_absence, decalage)

    def _dessiner_proprietaire(self, champs, cases, proprietaire, decalage) -> None:
        if not proprietaire.est_rempli:
            return

        if proprietaire.cocher_type:
            if proprietaire.type_personne == "morale":
                self._cocher(cases["morale"], decalage)
            else:
                self._cocher(cases["physique"], decalage)
                self._cocher(
                    cases["sexe_f"] if proprietaire.sexe == "F" else cases["sexe_m"],
                    decalage,
                )

        for cle, valeur in (
            ("identite", proprietaire.identite),
            ("siret", proprietaire.siret),
            ("voie_numero", proprietaire.voie_numero),
            ("voie_extension", proprietaire.voie_extension),
            ("voie_type", proprietaire.voie_type),
            ("voie_nom", proprietaire.voie_nom),
            ("code_postal", proprietaire.code_postal),
            ("commune", proprietaire.commune),
        ):
            self._ecrire(champs[cle], valeur, decalage)

        # Ligne « né(e) le … à … », présente uniquement dans le bloc nouveau propriétaire.
        if "naissance_lieu" in champs:
            self._ecrire_date(
                champs,
                ("naissance_jour", "naissance_mois", "naissance_annee"),
                proprietaire.naissance_date,
                decalage,
            )
            self._ecrire(champs["naissance_lieu"], proprietaire.naissance_lieu, decalage)

    def _dessiner_cession(self, donnees: CessionData, decalage) -> None:
        self._cocher(
            CASES_ANCIEN["ceder_destruction"]
            if donnees.pour_destruction
            else CASES_ANCIEN["ceder"],
            decalage,
        )
        self._ecrire_date(
            CESSION, ("jour", "mois", "annee"), donnees.date_cession, decalage
        )
        heure, minute = _eclater_heure(donnees.heure_cession)
        self._ecrire(CESSION["heure"], heure, decalage)
        self._ecrire(CESSION["minute"], minute, decalage)

        if donnees.certifie_situation:
            self._cocher(CASES_ANCIEN["certifie_situation"], decalage)
        if donnees.certifie_transformation:
            self._cocher(CASES_ANCIEN["certifie_transformation"], decalage)
        if donnees.certifie_vhu:
            self._cocher(CASES_ANCIEN["certifie_vhu"], decalage)
            self._ecrire(AGREMENT_VHU, donnees.agrement_vhu, decalage)

    def _dessiner_nouveau(self, donnees: CessionData, decalage) -> None:
        self._dessiner_proprietaire(NOUVEAU, CASES_NOUVEAU, donnees.nouveau, decalage)
        if donnees.nouveau_certifie:
            self._cocher(CASES_NOUVEAU["acquerir"], decalage)
            self._cocher(CASES_NOUVEAU["informe"], decalage)

    def _dessiner_signatures(self, donnees: CessionData, decalage) -> None:
        self._ecrire(SIGNATURE_ANCIEN["ville"], donnees.ville, decalage)
        self._ecrire(SIGNATURE_ANCIEN["date"], donnees.date_signature, decalage)
        if donnees.nouveau.est_rempli:
            self._ecrire(SIGNATURE_NOUVEAU["ville"], donnees.ville, decalage)
            self._ecrire(SIGNATURE_NOUVEAU["date"], donnees.date_signature, decalage)
        if donnees.opposition_prospection:
            self._cocher(CASE_OPPOSITION, decalage)

    # -- aide au calage ------------------------------------------------------
    def dessiner_grille(self) -> None:
        """Quadrillage de 10 pt gradué dans le repère du CERFA (origine bas-gauche).

        Le nombre lu sur le PDF est celui à recopier dans `cession_layout.py`.
        """
        self.set_line_width(0.15)
        self.set_font("Helvetica", "", 4)
        for y in range(0, int(A4_H_PT), 10):
            appuye = y % 50 == 0
            self.set_draw_color(150, 150, 255) if appuye else self.set_draw_color(
                228, 228, 244
            )
            self.line(0, y_fpdf(y), A4_L_PT, y_fpdf(y))
            if appuye:
                self.set_text_color(70, 70, 200)
                self.text(2, y_fpdf(y) - 1, str(y))
                self.text(A4_L_PT - 16, y_fpdf(y) - 1, str(y))
        for x in range(0, int(A4_L_PT), 10):
            appuye = x % 50 == 0
            self.set_draw_color(150, 150, 255) if appuye else self.set_draw_color(
                228, 228, 244
            )
            self.line(x, 0, x, A4_H_PT)
            if appuye:
                self.set_text_color(70, 70, 200)
                self.text(x + 1, y_fpdf(A4_H_PT - 6), str(x))
                self.text(x + 1, y_fpdf(4), str(x))
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)


def construire_overlay(
    donnees: CessionData, *, calage: bool = False, decalage=(0.0, 0.0)
) -> bytes:
    """Calque à deux pages : les deux exemplaires du CERFA ont la même mise en page."""
    pdf = OverlayCession()
    for _ in range(2):
        pdf.add_page()
        if calage:
            pdf.dessiner_grille()
        pdf.dessiner_donnees(donnees, decalage)
    return pdf.output(dest="S").encode("latin-1", "replace")


def remplir_cerfa(
    donnees: CessionData,
    *,
    calage: bool = False,
    decalage=(0.0, 0.0),
    chemin_cerfa: Path = CHEMIN_CERFA,
) -> bytes:
    """Renvoie le CERFA officiel rempli, prêt à être téléchargé."""
    if not chemin_cerfa.exists():
        raise FileNotFoundError(
            f"Formulaire CERFA introuvable : {chemin_cerfa}. "
            "Le fichier assets/cerfa_15776-02.pdf est-il bien présent ?"
        )

    calque = PdfReader(
        io.BytesIO(construire_overlay(donnees, calage=calage, decalage=decalage))
    )
    writer = PdfWriter(clone_from=PdfReader(str(chemin_cerfa)))
    for index, page in enumerate(writer.pages):
        page.merge_page(calque.pages[index], over=True)

    tampon = io.BytesIO()
    writer.write(tampon)
    return tampon.getvalue()
