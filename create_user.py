from supabase import create_client
import bcrypt
import streamlit as st

url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]

supabase = create_client(url, key)

password = input("pass de la cuenta nueva: ")
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

supabase.table('usuarios').insert({
    "username": input("user nuevo: "),
    "password": hashed_password
}).execute()    