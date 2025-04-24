import streamlit as st
from supabase import create_client, Client
import bcrypt
from datetime import datetime,timezone
import streamlit_cookies_manager as cookies_manager
import time

# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)



# Función para verificar credenciales
def verificar_login(username, password):
    try:
        response = supabase.table('usuarios').select('*').eq('username', username).execute()
        if not response.data:
            return False
        usuario = response.data[0]
        # Verificar contraseña hasheada
        if bcrypt.checkpw(password.encode('utf-8'), usuario['password'].encode('utf-8')):
            return True
        return False
    except Exception as e:
        st.error(f"Error de autenticación: {str(e)}")
        return False
    
# Función para guardar estado sesión


def cerrar_sesion():
    supabase.table("sesiones").delete().eq("username", st.session_state["usuario"]).execute()
    st.session_state.clear()  # Limpiar el estado de la sesión
    st.session_state["logout_forzado"] = True
    st.rerun()         


def guardar_estado_sesion(username, pagina, centro_id, subpagina):
    data = {
        "username": username,
        "pagina": pagina,
        "centro_seleccionado": centro_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subpagina": subpagina
    }    
    supabase.table("sesiones").upsert(data, on_conflict=["username"]).execute()    