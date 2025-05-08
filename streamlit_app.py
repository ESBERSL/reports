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
from streamlit_cookies_manager import EncryptedCookieManager
from interfaces import pantalla_inicio, pantalla_gestion, pantalla_gestion_cuadros
from zoneinfo import ZoneInfo
from auth import  verificar_login, guardar_estado_sesion

# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
cookies = EncryptedCookieManager(password=st.secrets["supabase"]["cook"])


if "pagina" not in st.session_state:
    st.session_state["pagina"] = "inicio"

           

def ahora_es():
    return datetime.now(ZoneInfo("Europe/Madrid"))


def pantalla_login():
    st.title("Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        print(username)
        
        if not cookies.ready():
            st.info("Cargando sesión... refresque la página si tarda mucho.")
            st.stop()   
        cookies['usuario'] = username
        print("Cookie de usuario guardada")
        cookies.save()
        print(cookies.get('usuario'))
        if verificar_login(username, password):
            st.session_state['autenticado'] = True
            st.session_state['usuario'] = username
            st.session_state['pagina'] = "inicio"
            guardar_estado_sesion(username, "inicio", None, None)
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# ------------------ FLUJO PRINCIPAL ------------------ #
# FLUJO PRINCIPAL
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state["usuario"] = None

if "logout_forzado" in st.session_state:
    st.session_state.pop("logout_forzado")
else:
    if not cookies.ready():
        st.info("Cargando sesión... refresque la página si tarda mucho.")
        st.stop()
    if not st.session_state['autenticado']:
        print("No autenticado")
        if "usuario" in cookies:
                print("Cookie de usuario encontrada")
                username = cookies["usuario"]
                print(username)
                if username:
                    resp = supabase.table("sesiones").select("*").eq("username", username).execute()
                    if resp.data:
                        sesion = resp.data[0]
                        ahora = ahora_es()
                        ultima = datetime.fromisoformat(sesion["timestamp"]).astimezone(ZoneInfo("Europe/Madrid"))
                        if (ahora - ultima).total_seconds() <= 8 * 3600:
                            st.session_state.update({
                                "autenticado": True,
                                "usuario": username,
                                "pagina": sesion["pagina"],
                                "centro_seleccionado": sesion["centro_seleccionado"],
                                "subpagina": sesion["subpagina"],
                                "cuadro_id": sesion["cuadro_id"]
                            })
                            if sesion["centro_seleccionado"]:
                                centro = supabase.table("centros").select("*").eq("id", sesion["centro_seleccionado"]).execute().data[0]
                                st.session_state["nombre_centro"] = centro["nombre"]
                        else:
                            supabase.table("sesiones").delete().eq("username", username).execute()   
if not st.session_state['autenticado']:
    pantalla_login()
elif st.session_state["pagina"] == "inicio":
    pantalla_inicio()
elif st.session_state["pagina"] == "gestion":
    pantalla_gestion()
elif st.session_state["pagina"] == "gestion_cuadros":
    pantalla_gestion_cuadros()    