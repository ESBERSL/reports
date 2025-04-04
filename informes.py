import pandas as pd
from docx import Document
from io import BytesIO
from supabase import create_client, Client
import streamlit as st


# Conexión a Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Ruta de la plantilla de Word (asegúrate de que exista en tu proyecto)
PLANTILLA_WORD = "tierras_plantilla.docx"

# Obtener los cuadros eléctricos de un centro
def obtener_cuadros(centro_id):
    response = supabase.table('cuadros').select('*').eq('centro_id', centro_id).execute()
    return pd.DataFrame(response.data)

# Función para modificar la plantilla de Word
def generar_informe_word(centro_id):
    # Cargar la plantilla de Word
    doc = Document(PLANTILLA_WORD)
    
    # Obtener los cuadros del centro
    df_cuadros = obtener_cuadros(centro_id)

    # Buscar la tabla donde se insertarán los datos
    tabla = None
    for t in doc.tables:
        if len(t.columns) == 3:  # Suponemos que la tabla objetivo tiene 3 columnas
            tabla = t
            break

    if not tabla:
        raise ValueError("No se encontró una tabla con 3 columnas en la plantilla.")

    # Agregar filas con los datos
    for _, row in df_cuadros.iterrows():
        row_cells = tabla.add_row().cells
        row_cells[0].text = str(row['numero'])
        row_cells[1].text = row['nombre']
        row_cells[2].text = str(row['tierra_ohmnios']) if row['tierra_ohmnios'] is not None else 'N/A'

    # Guardar el documento en memoria
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)  # Mover el cursor al inicio
    file_path = f"informe_centro_{centro_id}.docx"
    doc.save(file_path)

    return buffer

# Función para obtener el archivo Word generado
def obtener_word(centro_id):
    return generar_informe_word(centro_id)
