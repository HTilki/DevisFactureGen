from datetime import datetime

def get_reference(session_state):
    # Récupérer les initiales du client (première lettre de chaque mot du nom et prénom)
    initiales_client = f"{session_state['nom'][:1]}{session_state['prenom'][:1]}"
    # Récupérer la date du système au format AAAAMMJJ
    date_systeme = datetime.now().strftime("%Y%m%d")
    # Créer la référence en combinant les initiales du client et la date du système
    reference = f"{session_state['type_document']}_{initiales_client.upper()}_{date_systeme}"
    return reference
