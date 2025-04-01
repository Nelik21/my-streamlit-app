import streamlit as st
import pandas as pd

st.title("Desk viewer")

# 1) Initialiser la variable "validated" UNIQUEMENT si elle n’existe pas
if "validated" not in st.session_state:
    st.session_state.validated = False

if "file" not in st.session_state:
    st.session_state.file = None
# 2) Widget de drag-and-drop


if st.session_state.file is None:
    st.session_state.file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx", "xls"])

if st.session_state.file is not None and not st.session_state.validated:
    df = pd.read_excel(st.session_state.file)
    
    st.write("Aperçu du contenu :")
    st.dataframe(df)  # Affiche le tableau

    if st.button("Validate"):
        # Au clic, on passe validated=True
        st.session_state.validated = True
        # Optionnel : on relance le script depuis le début pour forcer l'interface à se mettre à jour
        st.rerun()

# 3) Si le fichier est chargé ET que validated == True
if st.session_state.file is not None and st.session_state.validated:
    # Désormais, on n'affiche plus le drag-and-drop, mais la nouvelle interface
    df = pd.read_excel(st.session_state.file)
    sales_rep = df["Trader Name"].unique()
    selected_rep = st.selectbox("Sélectionnez un commercial :", sales_rep)
    
    st.dataframe(df[df["Trader Name"]==selected_rep])


    
    