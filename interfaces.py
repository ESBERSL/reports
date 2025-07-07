import streamlit as st
from supabase import create_client, Client
from zoneinfo import ZoneInfo
from datetime import datetime
import pandas as pd

from auth import guardar_estado_sesion, cerrar_sesion
from database import (
    obtener_centros,
    obtener_cuadros,
    agregar_cuadro,
    eliminar_cuadro,
    actualizar_tierra,
    actualizar_aislamiento,
    actualizar_defectos
)
from informes import (
    obtener_word_tierras,
    obtener_word_aislamientos,
    generar_informe_word_bra,
    generar_informe_word_reparacion
)

# Conexión a la base de datos de Supabase
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


def pantalla_inicio():
    st.title("Lista de Centros")
    if st.button("Cerrar sesión"):
        cerrar_sesion()
        st.rerun()

    # Filtros
    provincia = st.selectbox("Filtrar por cliente", ["Todos", "Conselleria Alicante", "Conselleria Valencia", "Conselleria Castellón", "DIV", "Nous Espais", "Ayto Catarroja", "Ayto Torrent", "Ayto Aldaia"], key="provincia")
    busqueda = st.text_input("Buscar centro", key="busqueda")
    

    df = obtener_centros()
    df = df.sort_values(by="nombre")
    if provincia != "Todos":
        df = df[df["cliente"] == provincia]
    if busqueda:
        df = df[df["nombre"].str.contains(busqueda, case=False, na=False)]
        

    for _, row in df.iterrows():
        if st.button(f"Seleccionar {row['nombre']}", use_container_width=True):
            st.session_state.update({
                "centro_seleccionado": row["id"],
                "nombre_centro": row["nombre"],
                "pagina": "gestion"
            })
            guardar_estado_sesion(st.session_state["usuario"], "gestion", row["id"], None)
            st.rerun()


def pantalla_gestion():
    
    st.header(f"Centro: {st.session_state.get('nombre_centro','')}")
    centro_id = st.session_state["centro_seleccionado"]
    usuario = st.session_state["usuario"]

    def cb_seccion(c_id, user):
        val = st.session_state["centro_seccion_acometida"]
        supabase.from_("centros") \
            .update({"seccion_acometida": val}) \
            .eq("id", c_id) \
            .execute()

    def cb_calibre(c_id, user):
        val = st.session_state["centro_calibre_fusibles"]
        supabase.from_("centros") \
            .update({"calibre_fusibles": val}) \
            .eq("id", c_id) \
            .execute()

    def cb_potencia(c_id, user):
        val = st.session_state["centro_potencia_grupo"]
        supabase.from_("centros") \
            .update({"potencia_grupo": val}) \
            .eq("id", c_id) \
            .execute()
        
    # Limpiar claves previas
    for k in ("centro_seccion_acometida","centro_calibre_fusibles","centro_potencia_grupo"):
        st.session_state.pop(k, None)

    # Obtener datos del centro
    df = obtener_centros()
    fila = df[df["id"] == centro_id]
    datos = fila.iloc[0].to_dict() if not fila.empty else {}
# ——— Navegación ———
    if st.button("Cerrar sesión"):
            cerrar_sesion()
            st.rerun()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Volver a Listado de Centros"):
            st.session_state["pagina"] = "inicio"
            guardar_estado_sesion(usuario, "inicio", None, None)
            st.rerun()

    # Datos editables
    st.subheader("Datos del Centro")
    seccion = float(datos.get("seccion_acometida") or 0.0)
    calibre = float(datos.get("calibre_fusibles") or 0.0)
    potencia = float(datos.get("potencia_grupo")   or 0.0)

    seccion_acometida = st.number_input(
        "Sección acometida (mm²)", value=seccion, min_value=0.0, step=1.0,
        key="centro_seccion_acometida",
        on_change=cb_seccion,
        args=(centro_id, usuario)
    )
    calibre_fusibles = st.number_input(
        "Calibre fusibles (A)",    value=calibre, min_value=0.0, step=1.0,
        key="centro_calibre_fusibles",
        on_change=cb_calibre,
        args=(centro_id, usuario)
    )
    potencia_grupo = st.number_input(
        "Potencia grupo (kVA)",    value=potencia, min_value=0.0, step=1.0,
        key="centro_potencia_grupo",
        on_change=cb_potencia,
        args=(centro_id, usuario)
    )

    c1, c2 , c3 = st.columns(3)
    with c1:
        if st.button("Guardar datos del centro"):
            try:
                cid = int(centro_id)
            except ValueError:
                st.error(f"ID de centro inválido: {centro_id}")
            else:
                # Ejecutamos el update y capturamos la respuesta
                resp = supabase\
                    .from_("centros")\
                    .update({
                        "seccion_acometida": seccion_acometida,
                        "calibre_fusibles":   calibre_fusibles,
                        "potencia_grupo":     potencia_grupo,
                    })\
                    .eq("id", cid)\
                    .execute()
            st.success("Datos del centro actualizados correctamente.")
    # Gestionar cuadros

    with c2:
        if st.button("Gestionar cuadros"):
            # Actualizamos estado y salvamos en sesión
            st.session_state["pagina"] = "gestion_cuadros"
            guardar_estado_sesion(
                st.session_state["usuario"],
                "gestion_cuadros",
                centro_id,
                None
            )
            st.rerun()    

    st.divider()

    # Botones de informes
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Informe Tierras"):
            try:
                obtener_word_tierras(centro_id)
            except ValueError as e:
                st.error(str(e))
    with c2:
        if st.button("Informe Aislamientos"):
            try:
                obtener_word_aislamientos(centro_id)
            except ValueError as e:
                st.error(str(e))
    with c3:
        if st.button("Informe BRA"):
            generar_informe_word_bra(centro_id)
    with c4:
        if st.button("Informe para Reparación"):
            generar_informe_word_reparacion(centro_id)
def pantalla_gestion_cuadros():
    centro_id = st.session_state["centro_seleccionado"]
    usuario = st.session_state["usuario"]
    generales = [
    "PUNTERAS", "PEGATINA", "CIR SIN IDENTIFICAR", "OBTURADORES",
    "IDENTIF. COLORES", "SIN DIFERENCIAL", "DIFEREN NO ACTUA",
    "SELECTIVIDAD", "PROTECCION CONTRA SOBRECARGAS", "CERRADURA",
    "EMPALMES", "SECCIÓN INADECUADA", "SIN CORTE GENERAL",
    "AISLAMIENTO", "ARROLLAMIENTO", "CABLES SIN CANALIZAR",
    "CANALIZACIONES", "MAL ESTADO", "POLARIDAD INVERTIDA",
    "NO LEGIBLE", "CONT. DIRECTO", "TENSION CONTACTO",
    "GRUPO ELECTROGENO"
]
    tierras = ["PUERTAS/CHASIS", "MECANISMOS", "CUADRO", "MEDICION ELEVADA"]
    emergencias = ["NO HAY EMERGENCIA", "FALLA EMERGENCIA"]

    # ——— Navegación ———
    if st.button("Cerrar sesión"):
        cerrar_sesion()
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Volver a Listado de Centros"):
            st.session_state["pagina"] = "inicio"
            guardar_estado_sesion(usuario, "inicio", None, None)
            st.rerun()
    with col2:
        if st.button("← Volver a Gestión de Centro"):
            st.session_state["pagina"] = "gestion"
            guardar_estado_sesion(usuario, "gestion", centro_id, None)
            st.rerun()

    st.title(f"Gestión de Cuadros — {st.session_state['nombre_centro']}")

    # ——— Listado y edición de cuadros existentes ———
    df = obtener_cuadros(centro_id)
    

    def renderizar(defs_cat, regs):
        out = []
        for d in defs_cat:
            for r in regs:
                if r.startswith(d):
                    texto = r.replace("_", " (", 1) + (")" if "_" in r else "")
                    out.append(f"- {texto}")
        return "\n".join(out)

    for _, row in df.iterrows():
        cid = row["id"]
        st.subheader(f"{row['tipo']} {row['numero']} – {row['nombre']}")
        with st.expander("Editar cuadro"):
                tipo_edit = st.selectbox(
                    "Tipo",
                    ["CGBT","CS","CT","CC"],
                    index=["CGBT","CS","CT","CC"].index(row["tipo"]),
                    key=f"edit_tipo_{cid}"
                )
                numero_edit = st.number_input(
                    "Número",
                    value=row["numero"],
                    min_value=0, max_value=100, step=1,
                    key=f"edit_numero_{cid}"
                )
                nombre_edit = st.text_input(
                    "Nombre",
                    value=row["nombre"],
                    key=f"edit_nombre_{cid}"
                )
                if st.button("Guardar cambios", key=f"edit_cuadro_{cid}"):
                    supabase.from_("cuadros").update({
                        "tipo": tipo_edit,
                        "numero": numero_edit,
                        "nombre": nombre_edit,
                        "ultimo_usuario": usuario,
                        "ultima_modificacion": datetime.now().isoformat()
                    }).eq("id", cid).execute()
                    st.success("Cuadro actualizado.")
                    st.rerun()
        st.write(f"Tierra: {row['tierra_ohmnios'] or 0.0} Ω")
        st.write(f"Aislamiento: {row['aislamiento_megaohmnios'] or 0.0} MΩ")

        regs = row.get("defectos") or []
        st.write("**Defectos actuales:**")
        st.write("Generales:\n"   + renderizar(generales,    regs))
        st.write("Tierras:\n"     + renderizar(tierras,      regs))
        st.write("Emergencias:\n" + renderizar(emergencias,  regs))
        st.write("Anotaciones:\n" + (row.get("anotaciones") or ""))
        def cb_tierra(cuadro_id, user):
            val = st.session_state[f"t_{cuadro_id}"]
            actualizar_tierra(cuadro_id, val, user)

        def cb_aisla(cuadro_id, user):
            val = st.session_state[f"a_{cuadro_id}"]
            actualizar_aislamiento(cuadro_id, val, user)

        with st.expander("Editar mediciones"):
            t = st.number_input(
                "Tierra (Ω)",
                value=row["tierra_ohmnios"] or 0.0,
                min_value=0.0, step=1.0,
                key=f"t_{cid}",
                on_change=cb_tierra,
                args=(cid, usuario)
            )
            a = st.number_input(
                "Aislamiento (MΩ)",
                value=row["aislamiento_megaohmnios"] or 0.0,
                min_value=0.0, step=1.0,
                key=f"a_{cid}",
                on_change=cb_aisla,
                args=(cid, usuario)
            )
            if st.button("Guardar mediciones", key=f"gm_{cid}"):
                actualizar_tierra(cid, t, usuario)
                actualizar_aislamiento(cid, a, usuario)
                st.success("Mediciones actualizadas.")
                st.rerun()

        def cb_defectos(cuadro_id, user):
            seleccion = []
            # recorremos todas las categorías
            for d in generales + tierras + emergencias:
                if st.session_state.get(f"d_{cuadro_id}_{d}", False):
                    detalle = st.session_state.get(f"dt_{cuadro_id}_{d}", "").strip()
                    if detalle:
                        seleccion.append(f"{d}_{detalle}")
                    else:
                        seleccion.append(d)
            actualizar_defectos(cuadro_id, seleccion)

        with st.expander("Editar defectos"):
            seleccionados = []
            for d in generales + tierras + emergencias:
                chk = st.checkbox(
                    d,
                    value=any(r.startswith(d) for r in regs),
                    key=f"d_{cid}_{d}",
                    args=(cid, usuario)
                )
                if chk:
                    seleccionados.append(d)
            if st.button("Guardar defectos", key=f"gd_{cid}"):
                finales = [
                    d
                    for d in seleccionados
                ]
                actualizar_defectos(cid, finales)
                st.success("Defectos actualizados.")
                st.rerun()
        with st.expander("Editar Anotaciones"):
            anotaciones_edit = st.text_input(
                    "Anotaciones",
                    value=row["anotaciones"] or "",
                    key=f"edit_anot_{cid}"
                )
            if st.button("Guardar anotaciones", key=f"edit_cuadro_anot_{cid}"):
                    supabase.from_("cuadros").update({
                        "anotaciones": anotaciones_edit,
                    }).eq("id", cid).execute()
                    st.success("Cuadro actualizado.")
                    st.rerun()


        if st.button("Eliminar cuadro", key=f"del_{cid}"):
            eliminar_cuadro(cid)
            st.success("Cuadro eliminado.")
            st.rerun()

        st.divider()

   
    # 1) Campos básicos
    st.subheader("Añadir nuevo cuadro")

    # --- FORMULARIO SOLO SI NO ESTAMOS LIMPIANDO ---
    with st.form("form_nuevo_cuadro"):
        t0 = st.selectbox("Tipo", ["CGBT", "CS", "CT", "CC"], key="ntipo")
        n0 = st.number_input("Número", min_value=0, max_value=100, step=1, key="nnum")
        nm = st.text_input("Nombre", key="nnom")
        with st.expander("Añadir mediciones"):
            t1 = st.number_input("Tierra (Ω)", min_value=0.0, step=1.0, value=0.0, key="ntierra")
            a1 = st.number_input("Aislamiento (MΩ)", min_value=0.0, step=1.0, value=0.0, key="naisla")
        with st.expander("Añadir defectos"):
            defectos_nuevos = []


            st.markdown("### 🔧 Generales")
            for d in generales:
                marcado = st.checkbox(d, key=f"new_d_{d}", value=False)
                if marcado:
                    defectos_nuevos.append(d)

            st.markdown("### 🌍 Puesta a tierra")
            for d in tierras:
                marcado = st.checkbox(d, key=f"new_d_{d}", value=False)
                if marcado:
                    defectos_nuevos.append(d)

            st.markdown("### 🚨 Alumbrado de emergencia")
            for d in emergencias:
                marcado = st.checkbox(d, key=f"new_d_{d}", value=False)
                if marcado:
                    defectos_nuevos.append(d)
        with st.expander("Anotaciones"):
            anotaciones_nuevo = st.text_area("Anotaciones", key="new_anotaciones", value=" ")

        submit = st.form_submit_button("Añadir cuadro")

    if submit:
        agregar_cuadro(centro_id, t0, nm, n0, usuario, t1, a1, anotaciones_nuevo)
        respuesta = (
            supabase
            .from_("cuadros")
            .select("id")
            .eq("centro_id", centro_id)
            .eq("nombre", nm)
            .eq("numero", n0)
            .eq("tierra_ohmnios", t1)
            .eq("aislamiento_megaohmnios", a1)
            .single()
            .execute()
        )
        new_id = respuesta.data["id"] if respuesta.data else None

        if new_id is not None:
            defectos_finales = []
            for d in defectos_nuevos:
                    defectos_finales.append(d)
            actualizar_defectos(new_id, defectos_finales)
            st.session_state["limpiar_form"] = True
            defectos_finales = []
            defectos_nuevos = []
            st.success("Cuadro y defectos añadidos.")

        for d in generales + tierras + emergencias:
            for key in ("ntipo", "nnum", "nnom", "ntierra", "naisla", "new_anotaciones"):
                st.session_state.pop(key, None)
            for d in generales + tierras + emergencias:
                st.session_state.pop(f"new_d_{d}", None)
                st.session_state[f"new_d_{d}"] = False 
        st.session_state["nnom"]=""
        st.session_state["new_anotaciones"]=""
        st.session_state["ntierra"]=0.0
        st.session_state["naisla"]=0.0        
    # 4) Limpiar campos
        
        st.rerun()       
    

