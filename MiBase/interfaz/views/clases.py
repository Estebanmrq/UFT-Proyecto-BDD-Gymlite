# views/clases.py — Gestion de Clases y Reservas
import datetime
import streamlit as st
from database import (
    reservar_clase,
    registrar_nueva_classe,
    get_clases_disponibles,
    get_all_clases,
    get_all_proximas_clases,
    get_all_clases_pasadas,
    get_all_entrenadores,
    get_all_tipos,
    get_all_socios,
)

def _fmt(v):
    return str(v).replace("T", " ")[:16] if v else "—"

def render():
    st.title("🏋️ Reserva de Clases")
    st.caption("Administra las clases disponibles y reserva cupos")
    auth_role = st.session_state.auth.get("role") or "viewer"

    st.header("📋 Lista de Clases")
    
    with st.container():
        col1, col2 = st.columns([2, 4])
        
        with col1:
            # Mapa de filtros disponibles
            filtro_classes: dict[str, callable] = {
                "Proxima clases": get_all_proximas_clases,
                "Clases disponibles": get_clases_disponibles,
                "Clases pasadas": get_all_clases_pasadas,
                "Todas las clases": get_all_clases,
            }
            slctbx_filtro = st.selectbox(
                "Filtrar clases:",
                options=[title for title in filtro_classes.keys()],
                key="filtro_clases"
            )
        
        with col2:
            # Busqueda por texto libre sobre nombre o entrenador
            intxt_buscar = st.text_input(
                "Buscar por nombre o entrenador",
                placeholder="Ej: Yoga, Juan Perez",
                key="buscar_clases"
            )
        
    # Boton para admin que despliega formulario de nueva clase
    if auth_role == "admin":
        if st.button("➕ Agregar Clase", type="primary", width='stretch'):
            st.session_state.mostrar_formulario = True

    if auth_role == "admin" and st.session_state.get("mostrar_formulario", False):
        st.header("➕ Registrar Nueva Clase")
        registrar_form()
    
    try:
        clases = filtro_classes[slctbx_filtro]()

        if not clases:
            st.info("📭 No hay clases")
            return
        
        if intxt_buscar.strip():
            # Filtrado con busqueda similitud 
            search_term = intxt_buscar.lower().strip()
            clases_filtradas = []
            
            for clase in clases:
                nombre = clase.get("nombre", "").lower()
                entrenador = clase.get("entrenador", "").lower()
                tipo_clase = clase.get("tipo_clase", "").lower()
                
                if (search_term in nombre or 
                    search_term in entrenador or 
                    search_term in tipo_clase or
                    levenshtein_similarity(search_term, nombre) >= 0.2 or
                    levenshtein_similarity(search_term, entrenador) >= 0.2):
                    clases_filtradas.append(clase)
            
            clases = clases_filtradas

        if not clases:
            st.info("🔍 No se encontraron clases que coincidan con la busqueda")
            return

        for clase in clases:
            with st.container():
                st.markdown(f"## {clase.get('nombre', 'Clase')}")
                st.caption(clase.get('descripcion', '').strip())

                c1, c2, c3 = st.columns([3, 2, 1])

                with c1:
                    st.markdown(f"**Tipo:** {clase.get('tipo_clase', '—')}")
                    st.markdown(f"**Profesor:** {clase.get('entrenador', '—')}")

                with c2:
                    st.markdown(f"**Fecha/Hora:** {_fmt(clase.get('fecha_hora'))}")
                    st.markdown(f"**Duracion:** {clase.get('duracion_min', '—')} min")

                with c3:
                    cupos = int(clase.get('cupos_disponibles', 0) or 0)
                    total = int(clase.get('cupo_max', 0) or 0)
                    st.metric("Cupos", f"{cupos}/{total}")
                    
                # Popover para reservar un cupo
                with st.popover("Reservar", icon='📅'):
                    socios = get_all_socios()
                    
                    if not socios:
                        st.warning("No hay socios registrados")
                    else:
                        options_socios = {
                            f"{socio['id_socio']} - {socio.get('nombre', '')} {socio.get('apellido_p', '')} {socio.get('apellido_m', '')}".strip(): socio['id_socio']
                            for socio in socios
                        }
                        
                        socio_seleccionado = st.selectbox(
                            "Seleccionar Socio",
                            options=list(options_socios.keys()),
                            key=f"select_socio_{clase['id_clase']}",
                            help="Selecciona el socio que realizara la reserva"
                        )
                        
                        id_socio = options_socios.get(socio_seleccionado) if socio_seleccionado else None

                        # Logica de confirmacion de reserva
                        if st.button("Confirmar reserva", key=f"btn_res_{clase['id_clase']}", type="primary"):
                            # Validacion de seleccion de socio
                            if not id_socio:
                                st.error("Debes seleccionar un socio primero")
                            else:
                                ok, new_id, err = reservar_clase(int(id_socio), int(clase['id_clase']))

                                if ok:
                                    st.success(f"Reserva creada exitosamente ID {new_id}")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    # Normaliza mensaje de error para dar retroalimentacion clara
                                    msg_error = str(err or "").upper()

                                    if "UNIQUE" in msg_error:
                                        st.warning("Este socio ya tiene una reserva confirmada en esta clase")
                                    elif "CUPOS_AGOTADOS" in msg_error:
                                        st.error("Lo sentimos los cupos para esta clase se acaban de agotar")
                                    elif "SIN_SUSCRIPCION_ACTIVA" in msg_error:
                                        st.error("El socio no tiene una suscripcion activa vigente. Regulariza en Pagos")
                                    else:
                                        st.error(f"No se pudo reservar: {err}")

                st.divider()

    except Exception as e:
        st.error(f"Error al cargar clases: {e}")

def registrar_form() -> None:
    # Formulario para crear una nueva clase
    with st.form("form_nueva_clase", clear_on_submit=True):
        st.subheader("Informacion de la Clase")
        
        nombre = st.text_input("Nombre de la clase", 
                            placeholder="Ej: Yoga Matutino, CrossFit Avanzado")
        
        descripcion = st.text_area("Descripcion", 
                                placeholder="Descripcion opcional de la clase",
                                height=100)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha", min_value=datetime.datetime.now().date())
            hora = st.time_input("Hora", value=datetime.datetime.now().time())
            duracion_min = st.number_input("Duracion minutos", min_value=15, value=60, step=5)
        
        with col2:
            cupo_max = st.number_input("Cupo maximo", min_value=1, value=20, step=1)
            
            entrenadores = get_all_entrenadores()
            if entrenadores:
                options_entrenadores = {f"{ent['id_entrenador']} - {ent['nombre']} {ent['apellido']}": ent['id_entrenador'] for ent in entrenadores}
                entrenador_seleccionado = st.selectbox(
                    "Seleccionar Entrenador",
                    options=list(options_entrenadores.keys()),
                    help="Selecciona el entrenador que impartira la clase"
                )
                id_entrenador = options_entrenadores.get(entrenador_seleccionado)
            else:
                st.error("No hay entrenadores registrados")
                id_entrenador = None
            
            tipos = get_all_tipos()
            if tipos:
                options_tipos = {f"{tipo['id_tipo']} - {tipo['nombre']}": tipo['id_tipo'] for tipo in tipos}
                options_tipos_list = list(options_tipos.keys())
                
                tipo_seleccionado = st.selectbox(
                    "Tipo de Clase",
                    options=options_tipos_list,
                    help="Selecciona el tipo de clase"
                )
                
                id_tipo = options_tipos.get(tipo_seleccionado)
            else:
                st.error("No hay tipos de clase registrados")
                id_tipo = None
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("📝 Registrar Clase", type="primary")
        
        with col_btn2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.mostrar_formulario = False
                st.rerun()
        
        if submitted:
            errors = []
            if not nombre.strip():
                errors.append("El nombre de la clase es obligatorio")
            if not id_entrenador:
                errors.append("Debes seleccionar un entrenador")
            if not id_tipo:
                errors.append("Debes seleccionar un tipo de clase")
            if duracion_min <= 0:
                errors.append("La duracion debe ser mayor a 0")
            if cupo_max <= 0:
                errors.append("El cupo maximo debe ser mayor a 0")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                fecha_hora_str = f"{fecha} {hora.strftime('%H:%M:%S')}"
                
                with st.spinner("Registrando clase..."):
                    success, new_id, error = registrar_nueva_classe(
                        id_entrenador=int(id_entrenador),
                        id_tipo=int(id_tipo),
                        nombre=nombre.strip(),
                        descripcion=descripcion.strip() if descripcion else None,
                        fecha_hora=fecha_hora_str,
                        duracion_min=int(duracion_min),
                        cupo_max=int(cupo_max)
                    )
                
                if success:
                    st.success(f"Clase registrada exitosamente ID: {new_id}")
                    st.balloons()
                    st.session_state.mostrar_formulario = False
                    st.rerun()
                else:
                    if "FOREIGN KEY" in error:
                        st.error("Error el entrenador o tipo de clase no existe")
                    elif "UNIQUE" in error:
                        st.error("Error ya existe una clase con esos datos")
                    else:
                        st.error(f"Error al registrar: {error}")

def levenshtein_similarity(s1, s2):
    def _levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return _levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    distance = _levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 if max_len == 0 else 1 - (distance / max_len)