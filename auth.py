import streamlit as st
from supabase import create_client, Client
import bcrypt
from datetime import datetime,timezone, timedelta
import streamlit_cookies_manager as cookies_manager
import jwt 
import re
from postgrest.exceptions import APIError
from cookies import cookies 

# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
jwt_key= st.secrets["supabase"]["JWT"]


def crear_jwt(username, pagina=None, centro_id=None, subpagina=None):
    now = datetime.now(timezone.utc)
    payload = {
        "username": username,
        "pagina": pagina,
        "centro_seleccionado": centro_id,
        "timestamp": now.isoformat(),
        "subpagina": subpagina,
        "exp": now + timedelta(hours=8)  # Expira en 8 horas
    }
    token = jwt.encode(payload, jwt_key, algorithm="HS256")
    return token

def verificar_jwt(token):
    try:
        payload = jwt.decode(token, jwt_key, algorithms="HS256")
        return payload  # Devuelve todo el diccionario con la sesión
    except jwt.ExpiredSignatureError:
        st.error("La sesión ha expirado.")
    except jwt.InvalidTokenError:
        st.error("Token inválido.")
    return None

# Función para verificar credenciales
def verificar_login(username, password):
    try:
        response = supabase.table('usuarios').select('*').eq('username', username).single().execute()
        usuario = response.data
        if usuario and bcrypt.checkpw(password.encode('utf-8'), usuario['password'].encode('utf-8')):
            # Aquí puedes usar valores por defecto o personalizar según el usuario
            return crear_jwt(username, pagina="inicio", centro_id=None, subpagina=None)
        return None
    except APIError as e:
        if "PGRST116" in str(e):
            return None
        else:
            st.error(f"Error en Supabase: {e}")
            return None
    except Exception as e:
        st.error(f"Error general: {e}")
        return None

def cerrar_sesion(jwt_token):
    st.session_state.clear()
    st.session_state["logout_forzado"] = True
    cookies.pop("jwt")
    st.rerun()

def guardar_estado_sesion(username, pagina, centro_id, subpagina):
    jwt_token = crear_jwt(username, pagina, centro_id, subpagina)
    cookies["jwt"] = jwt_token
    cookies.save()
    
