import streamlit as st


if __name__ == "__main__":  

    # Configuración de la página
    st.set_page_config(page_title="Gestión de Centros", page_icon="🏢", layout="wide")
    st.markdown(
        """
        <style>
        .css-1aumxhk {
            background-color: #f0f2f5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    

from supabase import create_client, Client
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from cookies import main_flow, pantalla_login
from interfaces import pantalla_inicio, pantalla_gestion, pantalla_gestion_cuadros
# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


if "pagina" not in st.session_state:
    st.session_state["pagina"] = "inicio"

           






# ------------------ FLUJO PRINCIPAL ------------------ #
# FLUJO PRINCIPAL


main_flow()

if not st.session_state['autenticado']:
    pantalla_login()
elif st.session_state["pagina"] == "inicio":
    pantalla_inicio()
elif st.session_state["pagina"] == "gestion":
    pantalla_gestion()
elif st.session_state["pagina"] == "gestion_cuadros":
    pantalla_gestion_cuadros() 