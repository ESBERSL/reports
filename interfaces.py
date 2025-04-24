import streamlit as st
from supabase import create_client, Client
from zoneinfo import ZoneInfo
import pandas as pd
from datetime import datetime,timezone
from informes import obtener_word_tierras
from informes import obtener_word_aislamientos, generar_informe_word_bra
from auth import guardar_estado_sesion,cerrar_sesion
from database import obtener_centros,obtener_cuadros,agregar_cuadro, eliminar_cuadro, actualizar_aislamiento, actualizar_tierra, actualizar_defectos


# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


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
        if st.button(f"Seleccionar {row['nombre']}"):
            st.session_state["centro_seleccionado"] = row["id"]
            st.session_state["nombre_centro"] = row["nombre"]
            st.session_state["pagina"] = "gestion"
            st.session_state["subpagina"] = None
            guardar_estado_sesion(st.session_state["usuario"], "gestion", row["id"], None)
            st.rerun()



def pantalla_mediciones():
    guardar_estado_sesion(st.session_state["usuario"],st.session_state["pagina"],st.session_state["centro_seleccionado"], "mediciones")   
    centro_id = st.session_state["centro_seleccionado"]
    df_cuadros = obtener_cuadros(centro_id)

    # Verificar si hay cuadros y si la columna 'ultima_modificacion' existe
    if not df_cuadros.empty and "ultima_modificacion" in df_cuadros.columns:
        # Filtramos filas que tengan fecha válida
        df_filtrado = df_cuadros.dropna(subset=["ultima_modificacion"])
        if not df_filtrado.empty:
            # Convertimos la fecha a zona horaria de Madrid
            df_filtrado["ultima_modificacion"] = pd.to_datetime(
                df_filtrado["ultima_modificacion"], utc=True
            ).dt.tz_convert("Europe/Madrid")
            cuadro_reciente = df_filtrado.sort_values("ultima_modificacion", ascending=False).iloc[0]
            fecha_hora_mod = cuadro_reciente["ultima_modificacion"].strftime("%d/%m/%Y a las %H:%M")
            st.write(f"Última modificación por: {cuadro_reciente['ultimo_usuario']} el: {fecha_hora_mod}")
    else:
        st.write("Aún no hay cuadros creados.")

    for _, row in df_cuadros.iterrows():
        cuadro_id = row['id']
        st.subheader(f"Cuadro: {row['nombre']}")
        with st.expander("Editar cuadro"):
            nuevo_tipo = st.selectbox("Tipo", ["CGBT", "CS", "CT", "CC"], index=["CGBT", "CS", "CT", "CC"].index(row["tipo"]), key=f"edit_tipo_{cuadro_id}")
            nuevo_numero = st.number_input("Número", value=row["numero"], min_value=0, max_value=100, key=f"edit_numero_{cuadro_id}")
            nuevo_nombre = st.text_input("Nombre", value=row["nombre"], key=f"edit_nombre_{cuadro_id}")
            
            if st.button("Guardar cambios", key=f"guardar_edicion_{cuadro_id}"):
                actualizar_datos = {
                    "tipo": nuevo_tipo,
                    "numero": nuevo_numero,
                    "nombre": nuevo_nombre,
                    "ultimo_usuario": st.session_state["usuario"],
                    "ultima_modificacion": datetime.now(ZoneInfo("Europe/Madrid")).isoformat()
                }
                supabase.table('cuadros').update(actualizar_datos).eq('id', cuadro_id).execute()
                st.success("Cuadro actualizado correctamente.")
                st.rerun()
        tierra = st.number_input(
            "Medición de Tierra (Ω)",
            value=row["tierra_ohmnios"] or 0.0,
            key=f"tierra_input_{cuadro_id}",
            min_value=0.0,
            step=1.0,
            on_change=lambda:actualizar_tierra(cuadro_id, st.session_state[f"tierra_input_{cuadro_id}"], st.session_state["usuario"])            
        )
        aislamiento = st.number_input(
            "Medición de Aislamiento (MΩ)",
            value=row["aislamiento_megaohmnios"] or 0.0,
            key=f"aislamiento_input_{cuadro_id}",
            min_value=0.0,
            step=1.0,
            on_change=lambda:actualizar_aislamiento(cuadro_id, st.session_state[f"aislamiento_input_{cuadro_id}"], st.session_state["usuario"])
        )

        col1, col2 = st.columns([1, 1])

        with col2:
            with st.expander("Eliminar cuadro", expanded=False):
                st.warning("Esta acción no se puede deshacer.")
                if st.button("Confirmar eliminación", key=f"eliminar_btn_{cuadro_id}"):
                    eliminar_cuadro(cuadro_id)
                    st.success(f"Cuadro '{row['nombre']}' eliminado.")
                    st.rerun()
    
    st.subheader("Añadir Cuadro Eléctrico")
    tipo = st.selectbox("Tipo", ["CGBT", "CS", "CT", "CC"], key="tipo")
    numero = st.number_input("Número del cuadro", key="numero", min_value=0, max_value=100, step=1) 
    nombre = st.text_input("Nombre del cuadro", key="nombre")
    col1, col2 = st.columns([1, 1])
    with col1:
        tierra = st.number_input(
            "Medición de Tierra (Ω)",
            value=0.0,
            key=f"new_tierra_input",
            min_value=0.0,
            step=1.0,
        )
    with col2:
        aislamiento = st.number_input(
            "Medición de Aislamiento (MΩ)",
            value=0.0,
            key=f"new_aislamiento_input",
            min_value=0.0,
            step=1.0,
        )

    usuario = st.session_state['usuario']
    if st.button("Añadir Cuadro"):
        if nombre:
            try:
                agregar_cuadro(centro_id, tipo, nombre, numero, usuario, tierra, aislamiento)
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

def renderizar_defectos(defectos_categoria, registrados):
                lineas = []
                for defecto in defectos_categoria:
                    encontrados = [d for d in registrados if d.startswith(defecto)]
                    for d in encontrados:
                        if "_" in d:
                            nombre, detalle = d.split("_", 1)
                            lineas.append(f"- {nombre} ({detalle})")
                        else:
                            lineas.append(f"- {d}")
                return lineas

def pantalla_defectos():
    defectos_seleccionados = []
    detalles = {}
    # Categorías de defectos
    defectos_generales = [
        "PUNTERAS", "RIESGO ELEC", "CIR SIN IDENTIFICAR", "OBTURADORES", "IDENTIF. COLORES", 
        "SIN DIFERENCIAL", "DIFEREN NO ACTUA", "SELECTIVIDAD", "SOBRECARGAS", "CERRADURA", 
        "EMPALMES", "SECCIÓN INADECUADA", "SIN CORTE GENERAL", "AISLAMIENTO", "ARROLLAMIENTO", 
        "CABLES SIN CANALIZAR", "CANALIZACIONES", "MAL ESTADO", "POLARIDAD INVERTIDA", 
        "NO LEGIBLE", "CONT. DIRECTO", "TENSION CONTACTO", "GRUPO ELECTROGENO"
    ]

    defectos_tierras = ["PUERTAS/CHASIS", "MECANISMOS", "CUADRO", "MEDICION ELEVADA"]
    defectos_emergencias = ["NO HAY EMERGENCIA", "FALLA EMERGENCIA"]
    defectos_con_detalles = ["SELECTIVIDAD", "SOBRECARGAS", "SIN DIFERENCIAL", "DIFEREN NO ACTUA", "CERRADURA", "SECCIÓN INADECUADA", "ARROLLAMIENTO", "CABLES SIN CANALIZAR", "CANALIZACIONES", "MAL ESTADO", "NO LEGIBLE", "CONT. DIRECTO", "MECANISMOS", "NO HAY EMERGENCIA", "FALLA EMERGENCIA"]

    todos_defectos = defectos_generales + defectos_tierras + defectos_emergencias

    def mostrar_checkboxes(lista_defectos, categoria):
        st.write(f"**{categoria}:**")
        for defecto in lista_defectos:
            key_defecto = f"defecto_{cuadro_id}_{defecto}"
            value = any(d.startswith(defecto) for d in defectos_registrados)
            seleccionado = st.checkbox(defecto, key=key_defecto, value=value)
            if seleccionado:
                defectos_seleccionados.append(defecto)
                if defecto in defectos_con_detalles:
                    detalle_key = f"detalle_{cuadro_id}_{defecto}"
                    detalle_valor = ""
                    for d in defectos_registrados:
                        if d.startswith(f"{defecto}_"):
                            _, detalle_valor = d.split("_", 1)
                            break
                    detalles[defecto] = st.text_area(f"Detalles para {defecto}:", value=detalle_valor, key=detalle_key)

    def mostrar_checkboxes_nuevo(lista_defectos, categoria):
        st.write(f"**{categoria}:**")
        for defecto in lista_defectos:
            key_defecto = f"defecto_nuevo_{defecto}"
            seleccionado = st.checkbox(defecto, key=key_defecto)
            if seleccionado:
                defectos_seleccionados.append(defecto)
                if defecto in defectos_con_detalles:
                    detalle_key = f"detalle_nuevo_{defecto}"
                    detalle_valor = ""
                    detalles[defecto] = st.text_area(f"Detalles para {defecto}:", value=detalle_valor, key=detalle_key)                
    guardar_estado_sesion(st.session_state["usuario"], st.session_state["pagina"], st.session_state["centro_seleccionado"], "defectos")
    centro_id = st.session_state["centro_seleccionado"]
    nomb = st.session_state["nombre_centro"]
    st.title(f"Gestión de Defectos del Centro {nomb}")

    df_cuadros = obtener_cuadros(centro_id)

    

    if not df_cuadros.empty:
        for _, row in df_cuadros.iterrows():
            cuadro_id = row['id']
            st.subheader(f"Cuadro: {row['nombre']}")

            with st.expander("Editar cuadro"):
                nuevo_tipo = st.selectbox("Tipo", ["CGBT", "CS", "CT", "CC"], index=["CGBT", "CS", "CT", "CC"].index(row["tipo"]), key=f"edit_tipo_{cuadro_id}")
                nuevo_numero = st.number_input("Número", value=row["numero"], min_value=0, max_value=100, key=f"edit_numero_{cuadro_id}")
                nuevo_nombre = st.text_input("Nombre", value=row["nombre"], key=f"edit_nombre_{cuadro_id}")
                
                if st.button("Guardar cambios", key=f"guardar_edicion_{cuadro_id}"):
                    actualizar_datos = {
                        "tipo": nuevo_tipo,
                        "numero": nuevo_numero,
                        "nombre": nuevo_nombre,
                        "ultimo_usuario": st.session_state["usuario"],
                        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
                    }
                    supabase.table('cuadros').update(actualizar_datos).eq('id', cuadro_id).execute()
                    st.success("Cuadro actualizado correctamente.")
                    st.rerun()

            # Mostrar defectos actuales
            defectos_registrados = row.get("defectos", [])
            if defectos_registrados is None:
                defectos_registrados = []

            key_editar = f"editar_defectos_{cuadro_id}"
            if key_editar not in st.session_state:
                st.session_state[key_editar] = False

            

            if not st.session_state[key_editar]:
                if defectos_registrados:
                    # Mostrar defectos actuales
                    st.write("Defectos actuales:")
                    st.write("**Generales:**")
                    st.write("\n".join(renderizar_defectos(defectos_generales, defectos_registrados)))
                    st.write("**Tierras:**")
                    st.write("\n".join(renderizar_defectos(defectos_tierras, defectos_registrados)))
                    st.write("**Emergencias:**")
                    st.write("\n".join(renderizar_defectos(defectos_emergencias, defectos_registrados)))
                else:
                    st.write("No hay defectos registrados.")

                # Botón para iniciar edición
                if st.button("Editar defectos", key=f"btn_editar_{cuadro_id}"):
                    st.session_state[key_editar] = True
                    st.rerun()
            else:
                # Sección de edición
                st.write("Editar defectos:")
                

                mostrar_checkboxes(defectos_generales, "Generales")
                mostrar_checkboxes(defectos_tierras, "Tierras")
                mostrar_checkboxes(defectos_emergencias, "Emergencias")

                col_guardar, col_cancelar = st.columns(2)
                with col_guardar:
                    if st.button(f"Guardar defectos para cuadro", key=f"guardar_defectos_{cuadro_id}"):
                        defectos_finales = []
                        for defecto in defectos_seleccionados:
                            if defecto in detalles and detalles[defecto].strip():
                                defecto_con_detalle = f"{defecto}_{detalles[defecto].strip()}"
                                defectos_finales.append(defecto_con_detalle)
                            else:
                                defectos_finales.append(defecto)

                        actualizar_defectos(cuadro_id, defectos_finales)
                        st.success("Defectos actualizados correctamente.")
                        st.session_state[key_editar] = False
                        st.rerun()

                with col_cancelar:
                    if st.button("Cancelar edición", key=f"cancelar_defectos_{cuadro_id}"):
                        st.session_state[key_editar] = False
                        st.rerun()

            # Campos para eliminar el cuadro
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Eliminar cuadro", key=f"eliminar_btn_{cuadro_id}"):
                    eliminar_cuadro(cuadro_id)
                    st.success(f"Cuadro '{row['nombre']}' eliminado.")
                    st.rerun()
            st.divider()
    

    if st.button("Generar BRA"):
            generar_informe_word_bra(centro_id)

    # Opción para agregar nuevos cuadros
    st.subheader("Añadir Cuadro Eléctrico")
    tipo = st.selectbox("Tipo", ["CGBT", "CS", "CT", "CC"], key="tipo_nuevo")
    numero = st.number_input("Número del cuadro", key="numero_nuevo", min_value=0, max_value=100, step=1) 
    nombre = st.text_input("Nombre del cuadro", key="nombre_nuevo")
    usuario = st.session_state['usuario']

    with st.expander("Añadir defectos"):  
        mostrar_checkboxes_nuevo(defectos_generales, "Generales")
        mostrar_checkboxes_nuevo(defectos_tierras, "Tierras")
        mostrar_checkboxes_nuevo(defectos_emergencias, "Emergencias")

        
        def limpiar_campos():
        # Eliminar las claves asociadas con los checkboxes y el campo de nombre
            for k in list(st.session_state.keys()):
                if k.startswith("defecto_nuevo_") or k.startswith("detalle_nuevo_") or k in ["nombre_nuevo", "numero_nuevo", "tipo_nuevo"]:
                    del st.session_state[k]
        
        


    if st.button("Añadir Cuadro", key="añadir_cuadro"):
        if nombre:
            try:
                # Procesar la adición del cuadro
                agregar_cuadro(centro_id, tipo, nombre, numero, usuario)
                respuesta = supabase.table("cuadros")\
                    .select("id")\
                    .eq("nombre", nombre)\
                    .eq("numero", numero)\
                    .eq("centro_id", centro_id)\
                    .execute()
                
                cuadro_id = respuesta.data[0]["id"]

                defectos_finales = []
                for defecto in defectos_seleccionados:
                    if defecto in detalles and detalles[defecto].strip():
                        defecto_con_detalle = f"{defecto}_{detalles[defecto].strip()}"
                        defectos_finales.append(defecto_con_detalle)
                    else:
                        defectos_finales.append(defecto)
                actualizar_defectos(cuadro_id, defectos_finales)

                # Limpiar todos los campos y volver a renderizar
                limpiar_campos()

                # Limpiar específicamente los checkboxes y el campo nombre
                for defecto in defectos_generales + defectos_tierras + defectos_emergencias:
                    st.session_state[f"defecto_nuevo_{defecto}"] = False
                st.session_state["nombre_nuevo"] = ""  # Limpiar el nombre del cuadro

                st.rerun()

            except ValueError as e:
                st.error(str(e))
        else:
            st.warning("Debes completar todos los campos")


def pantalla_gestion(): 
    col1, col2, col3 = st.columns(3)
    with col1:     
        if st.button("Cerrar sesión"):
            cerrar_sesion()
            st.rerun()         
    with col2:
        if st.button("Volver al listado"):
            st.session_state["pagina"] = "inicio"
            st.session_state["centro_seleccionado"] = None
            guardar_estado_sesion(st.session_state["usuario"],st.session_state["pagina"],st.session_state["centro_seleccionado"], None)
            st.rerun()
    
    with col3: 
        if not st.session_state["subpagina"] == None:
            if st.button("Volver al selector de gestión"):
                st.session_state["pagina"] = "gestion"
                st.session_state["subpagina"] = None
                guardar_estado_sesion(st.session_state["usuario"],st.session_state["pagina"],st.session_state["centro_seleccionado"], None)
                st.rerun()       
    # Selector de gestion
    
    if st.session_state["subpagina"] == "mediciones":
        pantalla_mediciones()
    elif st.session_state["subpagina"] == "defectos":
        pantalla_defectos()
    else:    
        st.subheader(st.session_state["nombre_centro"])
        if st.button("Gestionar Mediciones"):
            st.session_state["subpagina"] = "mediciones"
            st.rerun()
        if st.button("Gestionar Defectos"):
            st.session_state["subpagina"] = "defectos"
            st.rerun()     
