from streamlit_cookies_manager import EncryptedCookieManager
import streamlit as st

# Inicializa una instancia única
cookies = EncryptedCookieManager(password=st.secrets["supabase"]["cook"])

# Asegúrate de que esté inicializado
if not cookies.ready():
    st.stop()