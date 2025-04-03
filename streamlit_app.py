import streamlit as st
from supabase import create_client, Client
import pandas as pd
import bcrypt
from datetime import datetime,timezone
from streamlit_javascript import st_javascript


# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def get_local_storage(key):
    value = st_javascript(f"JSON.parse(localStorage.getItem('{key}'))")
    return value if value not in [None, "null"] else None

def set_local_storage(key, value):
    st_javascript(f"localStorage.setItem('{key}', JSON.stringify({value}));")

def delete_local_storage(key):
    st_javascript(f"localStorage.removeItem('{key}');")

# Función para cargar el estado desde localStorage
def load_session_state():
    session_keys = ['autenticado', 'usuario', 'pagina', 'centro_seleccionado']
    
    if not st.session_state.get('session_loaded'):
        for key in session_keys:
            value = get_local_storage(key)
            if value is not None:
                st.session_state[key] = value
        st.session_state['session_loaded'] = True

# Función para guardar el estado en localStorage
def save_session_state():
    session_data = {
        'autenticado': st.session_state.get('autenticado'),
        'usuario': st.session_state.get('usuario'),
        'pagina': st.session_state.get('pagina'),
        'centro_seleccionado': st.session_state.get('centro_seleccionado')
    }
    
    for key, value in session_data.items():
        if value is not None:
            set_local_storage(key, value)
        else:
            delete_local_storage(key)


# Función para verificar credenciales
def verificar_login(username, password):
    try:
        response = supabase.table('usuarios').select('*').eq('username', username).execute()
        if not response.data:
            return False
        usuario = response.data[0]
        # Verificar contraseña hasheada
        if bcrypt.checkpw(password.encode('utf-8'), usuario['password'].encode('utf-8')):
            return True
        return False
    except Exception as e:
        st.error(f"Error de autenticación: {str(e)}")
        return False

# Función para obtener la lista de centros
def obtener_centros():
    response = supabase.table('centros').select('*').execute()
    return pd.DataFrame(response.data)

# Función para obtener los cuadros eléctricos de un centro
def obtener_cuadros(centro_id):
    response = supabase.table('cuadros').select('*').eq('centro_id', centro_id).execute()
    return pd.DataFrame(response.data)

# Función para insertar un nuevo cuadro
def agregar_cuadro(centro_id, tipo, nombre, numero, usuario):
    data = {
        "centro_id": centro_id,
        "tipo": tipo,
        "nombre": nombre,
        "numero": numero,
        "tierra_ohmnios": None,
        "aislamiento_megaohmnios": None,
        "ultimo_usuario": usuario,
        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
    }
    response = supabase.table('cuadros').insert(data).execute()
    return response

# ------------------ INTERFAZ DE USUARIO ------------------ #
def pantalla_login():
    st.title("Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if verificar_login(username, password):
            st.session_state['autenticado'] = True
            st.session_state['usuario'] = username
            st.session_state['pagina'] = "inicio"
            save_session_state()
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

def pantalla_inicio():
    st.title("Lista de Centros")
    
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        delete_local_storage('autenticado')
        delete_local_storage('usuario')
        delete_local_storage('pagina')
        delete_local_storage('centro_seleccionado')
        st.rerun()
    
    provincia = st.selectbox("Filtrar por provincia", ["Todas", "Alicante", "Valencia", "Castellón"])
    busqueda = st.text_input("Buscar centro")
    
    df_centros = obtener_centros()
    
    if provincia != "Todas":
        df_centros = df_centros[df_centros["provincia"] == provincia]
    
    if busqueda:
        df_centros = df_centros[df_centros["nombre"].str.contains(busqueda, case=False, na=False)]

    for _, row in df_centros.iterrows():
        if st.button(f"Gestionar {row['nombre']}"):
            st.session_state["centro_seleccionado"] = row["id"]
            st.session_state["pagina"] = "gestion"
            save_session_state()
            st.rerun()

def actualizar_cuadro(cuadro_id, tierra, aislamiento, usuario):
    data = {
        "tierra_ohmnios": tierra,
        "aislamiento_megaohmnios": aislamiento,
        "ultimo_usuario": usuario,
        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
    }
    supabase.table('cuadros').update(data).eq('id', cuadro_id).execute()

def pantalla_gestion():
    centro_id = st.session_state["centro_seleccionado"]
    
    st.title(f"Gestión del Centro {centro_id}")
    
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()
    
    if st.button("Volver al listado"):
        st.session_state["pagina"] = "inicio"
        st.session_state["centro_seleccionado"] = None
        save_session_state()
        st.rerun()

    df_cuadros = obtener_cuadros(centro_id)

    for _, row in df_cuadros.iterrows():
        if row['tipo'] == "CGBT":
            nom_cuadro= (row['nombre'])
        else:
            nom_cuadro= (f"{row['tipo']}{row['numero']}-{row['nombre']}")   
        st.subheader(f"Cuadro: {nom_cuadro}")
        
        tierra = st.number_input("Medición de Tierra (Ω)", value=row["tierra_ohmnios"] or 0.0, key=f"tierra_{row['id']}", min_value=0.0, step=1.0)
        aislamiento = st.number_input("Medición de Aislamiento (MΩ)", value=row["aislamiento_megaohmnios"] or 0.0, key=f"aislamiento_{row['id']}", min_value=0.0, step=1.0)
        
        if st.button(f"Actualizar {row['nombre']}", key=f"update_{row['id']}"):
            actualizar_cuadro(row["id"], tierra, aislamiento, st.session_state["usuario"])
            st.rerun()

    st.subheader("Añadir Cuadro Eléctrico")
    tipo = st.selectbox("Tipo", ["CGBT", "CS", "CT", "CC"], key="tipo")
    numero = st.number_input("Número del cuadro", key="numero",min_value=0.0, step=1.0) 
    nombre = st.text_input("Nombre del cuadro", key="nombre")
    usuario = st.session_state['usuario']
    if st.button("Añadir Cuadro"):
        if nombre:
            try:
                agregar_cuadro(centro_id, tipo, nombre, numero, usuario)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        else:
            st.warning("Debes completar todos los campos")

# ------------------ FLUJO PRINCIPAL ------------------ #
# Cargar el estado al inicio
load_session_state()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    pantalla_login()
else:
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "inicio"
    if "centro_seleccionado" not in st.session_state:
        st.session_state["centro_seleccionado"] = None

    if st.session_state["pagina"] == "inicio":
        pantalla_inicio()
    elif st.session_state["pagina"] == "gestion":
        pantalla_gestion()
    save_session_state()       
