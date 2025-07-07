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

# Leer datos desde un archivo Excel
excel_file = "datos_centros.xlsx"
if excel_file is not None:
    df = pd.read_excel(excel_file)

    # Renombrar columnas para que coincidan con los campos de la base de datos
    df = df.rename(columns={
        "nombre": "nombre",
        "direccion": "direccion",
        "pueblo": "pueblo",
        "cp": "cp",
        "telefono": "telf",
        "cliente": "cliente",
        "email": "email",
        "nif": "nif"
    })

    # Seleccionar solo las columnas necesarias
    campos_db = ["nombre", "direccion", "pueblo", "cp", "telf", "cliente", "email", "nif"]
    df = df[campos_db]

    # Insertar cada fila en la tabla 'centros'
    for _, row in df.iterrows():
        data = row.to_dict()
        supabase.table("centros").insert(data).execute()
    st.success("Datos añadidos a la base de datos correctamente.")

# Contar ocurrencias de 'ultimo_usuario' en la tabla 'cuadros'

# Obtener todos los registros usando paginación
# limit = 1000
# offset = 0
# usuarios = []
#
# while True:
#     resultado = supabase.table("cuadros").select("ultimo_usuario").range(offset, offset + limit - 1).execute()
#     data = resultado.data
#     if not data:
#         break
#     usuarios.extend([row["ultimo_usuario"] for row in data if row.get("ultimo_usuario")])
#     if len(data) < limit:
#         break
#     offset += limit
#
# contador = Counter(usuarios)
# print("Conteo de 'ultimo_usuario':")
# for usuario, cantidad in contador.items():
#     print(f"{usuario}: {cantidad}")

    