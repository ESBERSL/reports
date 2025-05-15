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

    from interfaces import pantalla_inicio, pantalla_gestion, pantalla_gestion_cuadros
    from auth import  verificar_login, guardar_estado_sesion, verificar_jwt

from supabase import create_client, Client
from datetime import datetime
from cookies import cookies 
from zoneinfo import ZoneInfo


# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
jwt_key= st.secrets["supabase"]["JWT"]
supabase: Client = create_client(url, key)


if "pagina" not in st.session_state:
    st.session_state["pagina"] = "inicio"

           

def ahora_es():
    return datetime.now(ZoneInfo("Europe/Madrid"))


def pantalla_login():
    st.title("Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if not cookies.ready():
            st.info("Cargando sesión... refresque la página si tarda mucho.")
            st.stop()

        jwt_token = verificar_login(username, password)
        if jwt_token:
            cookies["jwt"] = jwt_token
            cookies.save()
            st.session_state["autenticado"] = True
            st.session_state["jwt"] = jwt_token
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# ------------------ FLUJO PRINCIPAL ------------------ #
# FLUJO PRINCIPAL
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state["usuario"] = None

if "logout_forzado" in st.session_state or "logout_forzado" in cookies:
    if not cookies.ready():
        st.info("Cerrando sesión... refresque la página si tarda mucho.")
        st.stop()
    if "logout_forzado" in st.session_state:
        st.session_state.pop("logout_forzado")        
else:
    if not cookies.ready():
        st.info("Cargando sesión... refresque la página si tarda mucho.")
        st.stop()
    if not st.session_state['autenticado']:
        print("No autenticado")
        if "jwt" in cookies:
                print("Cookie de usuario encontrada")
                payload = verificar_jwt(cookies.get("jwt"))
                if payload:
                    username = payload["username"]
                    pagina = payload["pagina"]
                    subpagina = payload.get("subpagina")
                    centro = payload.get("centro_seleccionado")
                st.session_state.update({
                    "autenticado": True,
                    "jwt": cookies.get("jwt"),
                    "pagina": pagina,
                    "centro_seleccionado": centro,
                    "subpagina": subpagina,
                    "usuario": username
                })   
if not st.session_state['autenticado']:
    pantalla_login()
elif st.session_state["pagina"] == "inicio":
    pantalla_inicio()
elif st.session_state["pagina"] == "gestion":
    pantalla_gestion()
elif st.session_state["pagina"] == "gestion_cuadros":
    pantalla_gestion_cuadros()    