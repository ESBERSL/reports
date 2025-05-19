import streamlit as st
from supabase import create_client, Client
import bcrypt
from datetime import datetime,timezone, timedelta
import jwt 
import re
from postgrest.exceptions import APIError

# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
jwt_key= st.secrets["supabase"]["JWT"]


def crear_jwt(username):
    now = datetime.now(timezone.utc)
    payload = {
        "username": username,
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
        return None

# Función para verificar credenciales
def verificar_login(username, password):
    try:
        response = supabase.table('usuarios').select('*').eq('username', username).single().execute()
        usuario = response.data
        if usuario and bcrypt.checkpw(password.encode('utf-8'), usuario['password'].encode('utf-8')):
            # Aquí puedes usar valores por defecto o personalizar según el usuario
            return crear_jwt(username)
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




def guardar_estado_sesion(username, pagina, centro_id, subpagina):
    data = {
        "username": username,
        "pagina": pagina,
        "centro_seleccionado": centro_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subpagina": subpagina
    }    
    supabase.table("sesiones").upsert(data, on_conflict=["username"]).execute()    