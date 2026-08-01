"""Nettoyage des chaînes pour les polices coeur de fpdf 1.7.2 (latin-1 uniquement)."""

# Caractères courants issus d'un copier-coller (Word, web) qui n'existent pas en latin-1.
_SUBSTITUTIONS = {
    "’": "'",  # apostrophe courbe
    "‘": "'",
    "“": '"',
    "”": '"',
    "–": "-",  # tiret demi-cadratin
    "—": "-",
    "…": "...",
    " ": " ",  # espace insécable
    " ": " ",  # espace fine insécable
    "€": "EUR",
    "−": "-",
}


def assainir_latin1(valeur: object) -> str:
    """Rend une valeur imprimable par fpdf 1.7.2, sans jamais lever d'exception."""
    if valeur is None:
        return ""
    texte = str(valeur).strip()
    for source, cible in _SUBSTITUTIONS.items():
        texte = texte.replace(source, cible)
    return texte.encode("latin-1", "replace").decode("latin-1")
