import pandas as pd
from supabase import create_client, Client
import streamlit as st
import openpyxl


# ----------------------------
# CONFIGURA TU CONEXIÓN
# ----------------------------
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ----------------------------
# CARGA Y PROCESAMIENTO DEL EXCEL
# ----------------------------
def cargar_datos_excel(ruta_archivo):
    df = pd.read_excel(ruta_archivo)
    return df[["nombre", "CIF", "email", "pot"]]

# ----------------------------
# ACTUALIZACIÓN EN SUPABASE
# ----------------------------
def limpiar_campo(valor):
    """Limpia caracteres invisibles como \xa0, espacios múltiples y comas al final."""
    if pd.isna(valor):
        return None
    return str(valor).replace('\xa0', ' ').replace('', '').strip()

def actualizar_datos_centros(excel_path):
    df = pd.read_excel(excel_path)

    for _, row in df.iterrows():
        nombre_excel = row.get("nombre")

        if not nombre_excel:
            continue

        # Buscar el centro por nombre
        resultado = supabase.table("centros").select("id").eq("nombre", nombre_excel).execute()
        if not resultado.data:
            print(f"[NO ENCONTRADO] Centro: {nombre_excel}")
            continue

        centro_id = resultado.data[0]["id"]

        # Prepara el diccionario de campos a actualizar si existen
        updates = {}

        nif = limpiar_campo(row.get("CIF"))
        if nif:
            updates["nif"] = nif

        email = limpiar_campo(row.get("email"))
        if email:
            updates["email"] = email

        pot = limpiar_campo(row.get("pot"))
        if pot:
            try:
                updates["pot"] = pot
            except ValueError:
                print(f"[ERROR] Potencia no válida para '{nombre_excel}': '{pot}'")

        if updates:
            supabase.table("centros").update(updates).eq("id", centro_id).execute()
            print(f"[ACTUALIZADO] {nombre_excel}: {updates}")
        else:
            print(f"[SIN CAMBIOS] {nombre_excel}")

if __name__ == "__main__":
    ruta_excel = "datos_centros.xlsx"  # Cambia esto por la ruta real del archivo
    actualizar_datos_centros(ruta_excel)            