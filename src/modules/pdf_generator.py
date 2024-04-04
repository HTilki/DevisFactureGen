from datetime import datetime

from fpdf import FPDF


class DEVIS_FACTURE(FPDF):
    def __init__(self, session_state, secrets):
        super().__init__()
        self.type_document = session_state["type_document"]
        self.nom = session_state["nom"]
        self.prenom = session_state["prenom"]
        self.telephone = session_state["telephone"]
        self.email = session_state["email"]
        self.adresse = session_state["adresse"]
        self.marque = session_state["marque"].upper()
        self.modele = session_state["modele"].upper()
        self.immatriculation = session_state["immatriculation"].upper()
        self.nserie = session_state["nserie"]
        self.kilometrage = session_state["kilometrage"]
        self.ref = session_state["ref"]
        self.prestations = session_state["prestations"]
        self.montant_total_output = session_state["montant_total_output"]
        self.adresse_ent = secrets["adresse_ent"]
        self.email_ent = secrets["email_ent"]
        self.telephone_ent = secrets["telephone_ent"]
        self.siret = secrets["siret"]

    def header(self):
        # Ajouter le logo en haut à droite
        self.image("imgs/as_auto.png", 150, 10, 50)

        # Informations du client en dessous du logo à droite
        self.set_font("Arial", "", 10)
        self.set_xy(90, 70)
        self.cell(0, 5, f"{self.nom} {self.prenom}", 0, 1, "R")
        self.cell(0, 5, self.adresse, 0, 1, "R")
        self.cell(0, 5, f"Tel: {self.telephone}", 0, 1, "R")
        self.cell(0, 5, f"Email: {self.email}", 0, 1, "R")

        # Titre en haut à gauche
        self.set_xy(20, 20)
        self.set_font("Arial", "B", 20)
        self.cell(0, 10, self.type_document.upper(), 0, 1, "L")

        # Sous-titre en plus petit
        self.set_xy(10, 40)
        self.set_font("Arial", "B", 12)
        self.cell(10, 10, "AS Mécanique à domicile", 0, 1, "L")

        self.set_font("Arial", "", 10)

        # Réduire l'espacement entre les lignes
        self.ln(3)
        # Informations de l'entreprise
        self.cell(0, 5, self.adresse_ent, 0, 1, "L")
        self.cell(0, 5, f"Mail: {self.email_ent}", 0, 1, "L")
        self.cell(0, 5, f"Tél: {self.telephone_ent}", 0, 1, "L")
        self.cell(0, 5, f"SIRET: {self.siret}", 0, 1, "L")

        # Sauter une ligne avant la référence de la facture
        self.ln(10)

        # Ajouter la référence de la facture et la date
        date_actuelle = datetime.now().strftime("%d-%m-%Y")
        self.cell(0, 10, f"Référence facture : {self.ref}", 0, 1, "L")
        self.cell(0, 10, f"Date : {date_actuelle}", 0, 1, "L")

        # Sauter une ligne avant le tableau des informations sur le véhicule
        self.ln(8)

        # Ajouter le tableau des informations sur le véhicule
        self.set_font("Helvetica", "", 10)
        self.cell(0, 10, "Informations sur le véhicule", 0, 1, "C")

        # Définir les colonnes du tableau
        col_width = (self.w - 2 * self.l_margin) / 5
        self.cell(col_width, 10, "Marque", 1)
        self.cell(col_width, 10, "Modèle", 1)
        self.cell(col_width, 10, "Immatriculation", 1)
        self.cell(col_width, 10, "Numéro de série", 1)
        self.cell(col_width, 10, "Kilométrage", 1)

        # Aller à la ligne suivante
        self.ln(10)

        # Remplir le tableau avec les données du véhicule
        self.cell(col_width, 10, self.marque, 1)
        self.cell(col_width, 10, self.modele, 1)
        self.cell(col_width, 10, self.immatriculation, 1)
        self.cell(col_width, 10, self.nserie, 1)
        self.cell(col_width, 10, str(self.kilometrage), 1)

        # Aller à la ligne suivante
        self.ln(20)
        # Ajouter le tableau des prestations
        self.set_font("Helvetica", "", 10)
        self.cell(0, 10, "Liste des prestations", 0, 1, "C")

        # Définir les colonnes du tableau des prestations
        large_col_width = (self.w - 2 * self.l_margin) * 0.5
        small_col_width = (self.w - 2 * self.l_margin - large_col_width) / 3

        # Entêtes du tableau
        self.cell(large_col_width, 10, "Type de prestation", 1)
        self.cell(small_col_width, 10, "Quantité", 1)
        self.cell(small_col_width, 10, "Prix", 1)
        self.cell(small_col_width, 10, "Total", 1)
        self.ln(10)

        # Remplir le tableau des prestations avec les données du dataframe
        for _, row in self.prestations.iterrows():
            self.cell(large_col_width, 10, row["type_prestation"], 1)
            self.cell(small_col_width, 10, str(row["quantite"]), 1)
            self.cell(small_col_width, 10, str(row["prix"]) + " euros", 1)
            self.cell(small_col_width, 10, str(row["total_prest"]) + " euros", 1)
            self.ln(10)

        self.ln(20)
        # Ajouter le montant total
        self.set_font("Helvetica", "B", 12)
        self.cell(
            0,
            10,
            f"Le montant total à régler s'élève à : {self.montant_total_output}.",
            0,
            1,
            "C",
        )
