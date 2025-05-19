from streamlit_cookies_manager import EncryptedCookieManager
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from auth import verificar_login, guardar_estado_sesion 
from auth import verificar_jwt
from supabase import create_client, Client
from datetime import datetime, timezone


# Inicializa una instancia única
cookies = EncryptedCookieManager(password=st.secrets["supabase"]["cook"], prefix="session_")
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


# Asegúrate de que esté inicializado
if not cookies.ready():
    st.stop()

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
        if verificar_login(username, password):
            cookies["jwt"] = verificar_login(username, password)
            cookies.save()
            st.session_state['autenticado'] = True
            st.session_state['usuario'] = username
            st.session_state['pagina'] = "inicio"
            guardar_estado_sesion(username, "inicio", None, None)
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos") 

def cerrar_sesion(username):
    st.session_state.clear()
    st.session_state["logout_forzado"] = True
    cookies["jwt"] = ""
    cookies.pop("jwt", None)
    cookies.save()
    try:
        response = supabase.table("sesiones").delete().eq("username", username).execute()
        if response.data:
            print(f"Sesión de usuario '{username}' eliminada correctamente.")
            return True
        else:
            print(f"No se encontró sesión para el usuario '{username}' o ya fue eliminada.")
            return False
    except Exception as e:
        print(f"Error al cerrar sesión de '{username}': {e}")
        return False
    st.rerun()            


def main_flow():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
        st.session_state["usuario"] = None

    if "logout_forzado" in st.session_state:
        if not cookies.ready():
            st.info("Cargando sesión... refresque la página si tarda mucho.")
            st.stop()
            st.session_state.pop("logout_forzado")
    else:
        if not cookies.ready():
            st.info("Cargando sesión... refresque la página si tarda mucho.")
            st.stop()
        if not st.session_state['autenticado']:
            print("No autenticado")
            if "jwt" in cookies and cookies["jwt"] != "":
                    print("Cookie de usuario encontrada")
                    username = verificar_jwt(cookies["jwt"])["username"]
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
                                    "cuadro_id": sesion["cuadro_id"]
                                })
                                if sesion["centro_seleccionado"]:
                                    centro = supabase.table("centros").select("*").eq("id", sesion["centro_seleccionado"]).execute().data[0]
                                    st.session_state["nombre_centro"] = centro["nombre"]
                            else:
                                supabase.table("sesiones").delete().eq("username", username).execute()   
           