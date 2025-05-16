import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime,timezone

# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Función para obtener la lista de centros
def obtener_centros():
    response = supabase.table('centros').select('*').execute()
    return pd.DataFrame(response.data)

# Función para obtener los cuadros eléctricos de un centro
def obtener_cuadros(centro_id):
    response = supabase.table('cuadros').select('*').eq('centro_id', centro_id).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
    # Definimos el orden de tipos
        orden_tipo = {"CGBT": 0, "CS": 1, "CT": 2, "CC": 3}
        # Añadimos columna auxiliar para orden
        df["orden_tipo"] = df["tipo"].map(orden_tipo).fillna(99)
        df = df.sort_values(by=["orden_tipo", "numero"]).reset_index(drop=True)
    return df



def obtener_defectos(centro_id):
    cuadros_df = obtener_cuadros(centro_id)
    lista_defectos = []
    print(centro_id)

    for _, cuadro in cuadros_df.iterrows():
        nombre_cuadro = cuadro["nombre"]
        cuadro_id = cuadro["id"]
        defectos_str = cuadro.get("defectos")
        
        if isinstance(defectos_str, list):
             defectos_nombres = [d.strip() for d in defectos_str if isinstance(d, str) and d.strip()]
        else:
             defectos_nombres = [d.strip() for d in str(defectos_str).split(",") if d.strip()]

        for nombre in defectos_nombres:
            nombre_base = nombre.split("_")[0] 
            respuesta = supabase.table("defectos").select("nombre_defecto_normalizado, itc").eq("defecto_original", nombre_base).execute()
            if respuesta.data:
                defecto = respuesta.data[0]
                lista_defectos.append({
                    "cuadro": nombre_cuadro,
                    "nombre_normalizado": defecto["nombre_defecto_normalizado"],
                    "itc": defecto["itc"],
                    "cuadro_id": cuadro_id
                })
            else:
                print(f"[AVISO] Defecto no encontrado en diccionario: '{nombre_base}' (cuadro: {nombre_cuadro})")

    return lista_defectos

# Función para insertar un nuevo cuadro

def agregar_cuadro(centro_id, tipo, nombre, numero, usuario, tierra, aislamiento):
    data = {
        "centro_id": centro_id,
        "tipo": tipo,
        "nombre": nombre,
        "numero": numero,
        "tierra_ohmnios": tierra,
        "aislamiento_megaohmnios": aislamiento,
        "ultimo_usuario": usuario,
        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
        }
    response = supabase.table('cuadros').insert(data).execute()
    return response

def eliminar_cuadro(cuadro_id):
    supabase.table('cuadros').delete().eq('id', cuadro_id).execute()


def actualizar_cuadro(cuadro_id, tierra, aislamiento, usuario):
    data = {
        "tierra_ohmnios": tierra,
        "aislamiento_megaohmnios": aislamiento,
        "ultimo_usuario": usuario,
        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
      
    }
    supabase.table('cuadros').update(data).eq('id', cuadro_id).execute()


def actualizar_tierra(cuadro_id, tierra, usuario):
    data = {
        "tierra_ohmnios": tierra,
        "ultimo_usuario": usuario,
        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
      
    }
    print(st.session_state)
    supabase.table('cuadros').update(data).eq('id', cuadro_id).execute()

def actualizar_aislamiento(cuadro_id,aislamiento, usuario):
    data = {
        "aislamiento_megaohmnios": aislamiento,
        "ultimo_usuario": usuario,
        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
      
    }
    print(st.session_state)
    supabase.table('cuadros').update(data).eq('id', cuadro_id).execute()

def actualizar_defectos(cuadro_id, defectos_lista):
    supabase.table("cuadros").update({
        "defectos": defectos_lista
    }).eq("id", cuadro_id).execute()

def obtener_datos_cuadro(cuadro_id):
    response = supabase.table("cuadros").select("tipo, numero").eq("id", cuadro_id).single().execute()
    
    if response.data:
        return response.data["tipo"], response.data["numero"]
    else:
        return None, None