import streamlit as st
from supabase import create_client, Client
import pandas as pd
import bcrypt
from datetime import datetime,timezone, timedelta
import time
from informes import obtener_word_tierras
from informes import obtener_word_aislamientos
import streamlit_cookies_manager as cookies_manager

st.set_page_config(
    page_title="Gestión de Centros",  # Nombre de la pestaña en el navegador
    page_icon="🏢",  # Icono de la pestaña 
)

cookies = cookies_manager.CookieManager()


# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


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

# Función para guardar estado sesión
def guardar_estado_sesion(username, pagina, centro_id):
    data = {
        "username": username,
        "pagina": pagina,
        "centro_seleccionado": centro_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    supabase.table("sesiones").upsert(data, on_conflict=["username"]).execute()
    cookies["usuario"] = username
    cookies["pagina"] = pagina
    cookies["centro_seleccionado"] = centro_id
    cookies["timestamp"] = datetime.now(timezone.utc).isoformat()
    cookies.save(
    same_site="None",  # Necesario para cookies de terceros
    secure=True         # Asegura que las cookies solo se envíen a través de HTTPS
    )

def recuperar_sesion_si_existe():
    if "usuario" in cookies:
        username = cookies["usuario"]
        response = supabase.table("sesiones").select("*").eq("username", username).execute()
        if response.data:
            sesion = response.data[0]
            timestamp = datetime.fromisoformat(sesion["timestamp"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - timestamp < timedelta(hours=8):
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = username
                st.session_state["pagina"] = sesion.get("pagina", "inicio")
                st.session_state["centro_seleccionado"] = sesion.get("centro_seleccionado", None)



def cerrar_sesion():
    supabase.table("sesiones").delete().eq("username", st.session_state["usuario"]).execute()
    cookies.clear()  # Limpiar las cookies)
    st.session_state.clear()  # Limpiar el estado de la sesión
    st.rerun()

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
            guardar_estado_sesion(username, "inicio", None)
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

def pantalla_inicio():
    st.title("Lista de Centros")
    
    if st.button("Cerrar sesión"):
        cerrar_sesion()
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
            st.session_state["nombre_centro"] = row["nombre"]
            st.session_state["pagina"] = "gestion"
            guardar_estado_sesion(st.session_state["usuario"], "gestion", row["id"])
            st.rerun()

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

def pantalla_gestion():
    centro_id = st.session_state["centro_seleccionado"]
    nomb=st.session_state["nombre_centro"]
    st.title(f"Gestión del Centro {nomb}")
    
    if st.button("Cerrar sesión"):
        cerrar_sesion()
        st.rerun()
    
    if st.button("Volver al listado"):
        st.session_state["pagina"] = "inicio"
        st.session_state["centro_seleccionado"] = None
        st.rerun()

    df_cuadros = obtener_cuadros(centro_id)
        
    for _, row in df_cuadros.iterrows():
        cuadro_id = row['id']
        st.subheader(f"Cuadro: {row['nombre']}")

        # Campos de entrada únicos
        tierra = st.number_input(
            "Medición de Tierra (Ω)",
            value=row["tierra_ohmnios"] or 0.0,
            key=f"tierra_input_{cuadro_id}",
            min_value=0.0,
            step=1.0
        )

        aislamiento = st.number_input(
            "Medición de Aislamiento (MΩ)",
            value=row["aislamiento_megaohmnios"] or 0.0,
            key=f"aislamiento_input_{cuadro_id}",
            min_value=0.0,
            step=1.0
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Actualizar", key=f"actualizar_btn_{cuadro_id}"):
                actualizar_cuadro(cuadro_id, tierra, aislamiento, st.session_state["usuario"])
                st.rerun()

        with col2:
            with st.expander("Eliminar cuadro", expanded=False):
                st.warning("Esta acción no se puede deshacer.")
                if st.button("Confirmar eliminación", key=f"eliminar_btn_{cuadro_id}"):
                    eliminar_cuadro(cuadro_id)
                    st.success(f"Cuadro '{row['nombre']}' eliminado.")
                    st.rerun()

    st.subheader("Añadir Cuadro Eléctrico")
    tipo = st.selectbox("Tipo", ["CGBT", "CS", "CT", "CC"], key="tipo")
    numero = st.number_input("Número del cuadro", key="numero",min_value=0,max_value=100, step=1) 
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
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Generar Informe Tierras"):
            obtener_word_tierras(centro_id)

    with col2:
        if st.button("Generar Informe Aislamientos"):
            obtener_word_aislamientos(centro_id)        
    
        


# ------------------ FLUJO PRINCIPAL ------------------ #
# Cargar el estado al inicio

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
 
if not st.session_state['autenticado']:
    time.sleep(2) 
    if cookies.get("usuario"):
        username = cookies.get('usuario')
        if username:
            # Comprobar si tiene sesión guardada reciente
            resp = supabase.table("sesiones").select("*").eq("username", username).execute()
            if resp.data:
                sesion = resp.data[0]
                x = supabase.table("centros").select("*").eq("id", sesion["centro_seleccionado"]).execute()
                cent = x.data[0]
                print (cent["nombre"])
                ahora = datetime.now(timezone.utc)
                ultima = datetime.fromisoformat(sesion["timestamp"])
                if (ahora - ultima).total_seconds() <= 8 * 3600:  # 8 horas
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = username
                    st.session_state['pagina'] = sesion["pagina"]
                    st.session_state['centro_seleccionado'] = sesion["centro_seleccionado"] 
                    st.session_state['nombre_centro'] = cent["nombre"]

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
