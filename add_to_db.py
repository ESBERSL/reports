import pandas as pd
from supabase import create_client, Client
import streamlit as st
import openpyxl
from collections import Counter

# ----------------------------
# CONFIGURA TU CONEXIÓN
# ----------------------------
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


# Contar ocurrencias de 'ultimo_usuario' en la tabla 'cuadros'

# Obtener todos los registros usando paginación
limit = 1000
offset = 0
usuarios = []

while True:
    resultado = supabase.table("cuadros").select("ultimo_usuario").range(offset, offset + limit - 1).execute()
    data = resultado.data
    if not data:
        break
    usuarios.extend([row["ultimo_usuario"] for row in data if row.get("ultimo_usuario")])
    if len(data) < limit:
        break
    offset += limit

contador = Counter(usuarios)
print("Conteo de 'ultimo_usuario':")
for usuario, cantidad in contador.items():
    print(f"{usuario}: {cantidad}")