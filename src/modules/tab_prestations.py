import pandas as pd
import streamlit as st


def tab_prestations() -> pd.DataFrame:
    """Display an editable table based on `st.data_editor` that contains information about the invoice."""
    data_init = pd.DataFrame(
        {
            "type_prestation": ["None"],
            "quantite": [None],
            "prix": [None],
            "total_prest": [None],
        }
    )
    data_init["prix"] = data_init["prix"].astype(float)
    data_init["total_prest"] = data_init["total_prest"].astype(float)
    config = {
        "type_prestation": st.column_config.TextColumn("Prestation 🔧", default=""),
        "quantite": st.column_config.NumberColumn(
            "Quantité 👨🏽‍🔧", width="small", default=1, min_value=0
        ),
        "prix": st.column_config.NumberColumn(
            "Prix 💶", width="small", min_value=0, max_value=100000
        ),
        "total_prest": st.column_config.NumberColumn(
            "Total 💸", width="small", min_value=0, max_value=100000
        ),
    }
    df = st.data_editor(
        data_init[1:],
        column_config=config,
        num_rows="dynamic",
        use_container_width=True,
        key="data_edit",
    )
    return df
