import pandas as pd
from docx import Document
from io import BytesIO
from supabase import create_client, Client
import streamlit as st
from datetime import datetime

# Conexión a Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


def obtener_datos_centro(centro_id):
    response = supabase.table('centros').select('*').eq('id', centro_id).execute()
    
    if response.data:
        return response.data[0]  # Retorna el primer resultado
    else:
        return {"nombre": "Desconocido", "direccion": "Desconocida"}

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
    datos_centro = obtener_datos_centro(centro_id)
    nombre_centro = datos_centro["nombre"]
    direccion_centro = datos_centro["direccion"]
    cp_centro = str(int(float(datos_centro["cp"])))
    provincia_centro = datos_centro["provincia"]
    pueblo_centro = datos_centro["pueblo"]
    fecha_actual = datetime.now()

    df_cuadros = obtener_cuadros(centro_id)
    medidas_tierra = df_cuadros["tierra_ohmnios"].tolist()

    # Analizar la medición más alta y comparar con 48
    medida_maxima = max(medidas_tierra)
    informe_estado = "Favorable" if medida_maxima <= 48 else "Desfavorable"

    reemplazos = {
        "[NOMBRE]": nombre_centro,
        "[DIRECCION]": direccion_centro,
        "[CP]": cp_centro,
        "[PROVINCIA]": provincia_centro,
        "[PUEBLO]": pueblo_centro,
        "[RESULTADO]": informe_estado,
        "[FECHA]": fecha_actual.strftime("%d/%m/%Y")

    }
    for paragraph in doc.paragraphs:
        for placeholder, valor in reemplazos.items():
            for run in paragraph.runs:
                if placeholder in run.text:
                    run.text = run.text.replace(placeholder, valor)

    # Reemplazar en las tablas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        for placeholder, valor in reemplazos.items():
                            if placeholder in run.text:
                                run.text = run.text.replace(placeholder, valor)
    # Reemplazar en los encabezados (headers)
    for section in doc.sections:
        for header in section.header.paragraphs:
            for run in header.runs:
                for placeholder, valor in reemplazos.items():
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, valor)  


    # Obtener los cuadros del centro
    df_cuadros = obtener_cuadros(centro_id)

    # Buscar la tabla donde se insertarán los datos
    tabla = None
    for t in doc.tables:
        if len(t.columns) == 3:  # la tabla objetivo tiene 3 columnas
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
    file_path = "tmp/informe.docx"
    doc.save(file_path)
    with open("/tmp/informe.docx", "wb") as f:
        f.write(buffer.read())
      #output_pdf = "/tmp/informe.pdf"
      #pypandoc.download_pandoc()
      #pypandoc.convert_file("/tmp/informe.docx", to='pdf', outputfile=output_pdf)
    
    
    direccion_centro = datos_centro["direccion"]
    cp_centro = str(int(float(datos_centro["cp"])))
    provincia_centro = datos_centro["provincia"]
    fname = f"{fecha_actual.strftime('%Y-%m-%d')}_{datos_centro['nombre'].split('_')[0]}_InfTierras"
    with open("/tmp/informe.docx", "rb") as pdf_file:
        st.download_button("Descargar Informe", pdf_file, file_name=(f"{fname}.docx"), mime="application/docx")

    
# Función para obtener el archivo Word generado
def obtener_word(centro_id):
    return generar_informe_word(centro_id)
