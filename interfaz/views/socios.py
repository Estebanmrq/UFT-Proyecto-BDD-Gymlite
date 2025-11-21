# views/socios.py — Gestion de Socios (CRUD)
import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import (
    get_all_socios, buscar_socio_por_rut, crear_socio, actualizar_socio, eliminar_socio
)

# =========================
# Helpers
# =========================

def _rut_valido(rut: str) -> bool:
    # Valida largo minimo para un rut basico
    return bool(rut and len(rut.strip()) >= 9)


def _to_iso(d: date | str) -> str:
    # Convierte una fecha a formato ISO para guardar en la base de datos
    if isinstance(d, date):
        return d.isoformat()
    try:
        return datetime.strptime(str(d), "%Y-%m-%d").date().isoformat()
    except Exception:
        return str(d)


# =========================
# UI principal
# =========================

def render():
    st.title("👥 Gestion de Socios")
    st.caption("Administra informacion de los socios del gimnasio")

    tab_listar, tab_registrar, tab_buscar = st.tabs(
        ["📋 Listar Todos", "➕ Registrar Nuevo", "🔍 Buscar / Editar / Eliminar"]
    )

    # ------------------------------------------------------------
    # TAB 1: LISTAR TODOS
    # ------------------------------------------------------------
    with tab_listar:
        st.subheader("Listado completo de socios")

        if st.button("🔄 Refrescar Lista"):
            st.rerun()
    
        try:
            socios = get_all_socios()
            if socios:

                # Se renombra para mostrar columnas mas legibles
                df = pd.DataFrame(socios).rename(
                    columns={
                        "id_socio": "ID",
                        "apellido_p": "Apellido P.",
                        "apellido_m": "Apellido M.",
                        "telefono": "Telefono",
                        "direccion": "Direccion",
                        "fecha_nac": "Fecha Nac.",
                    }
                )

                st.dataframe(df, width='stretch', hide_index=True)

                # Muestra pequeñas metricas del listado
                c1, c2, c3 = st.columns(3)
                c1.metric("Total socios", len(socios))
                c2.metric("Con telefono", sum(1 for s in socios if s.get("telefono")))
                c3.metric("Con direccion", sum(1 for s in socios if s.get("direccion")))
            else:
                st.info("📭 No hay socios registrados. Usa Registrar Nuevo.")
        except Exception as e:
            st.error(f"❌ Error al cargar socios: {e}")

    # ------------------------------------------------------------
    # TAB 2: REGISTRAR NUEVO
    # ------------------------------------------------------------
    with tab_registrar:
        st.subheader("Registrar nuevo socio")

        # Formulario de registro de socio
        with st.form("form_crear_socio", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                rut = st.text_input("RUT *", placeholder="12345678-9")
                nombre = st.text_input("Nombre *", placeholder="Juan")
                apellido_p = st.text_input("Apellido Paterno *", placeholder="Perez")
            with c2:
                apellido_m = st.text_input("Apellido Materno", placeholder="Gonzalez")
                fecha_nac = st.date_input(
                    "Fecha de Nacimiento *",
                    min_value=date(1920, 1, 1),
                    max_value=date.today(),
                    value=date(2000, 1, 1),
                )

            st.markdown("---")

            c3, c4 = st.columns(2)
            with c3:
                telefono = st.text_input("Telefono", placeholder="+56912345678")
            with c4:
                direccion = st.text_area("Direccion", placeholder="Av. Providencia 123, Santiago", height=100)

            submitted = st.form_submit_button("✅ Registrar Socio", type="primary", width='stretch')

        if submitted:
            # Validaciones basicas antes de crear en la base de datos
            if not all([rut, nombre, apellido_p, fecha_nac]):
                st.error("⚠️ Completa los campos obligatorios")
            elif not _rut_valido(rut):
                st.error("⚠️ El RUT debe tener al menos 9 caracteres")
            else:
                try:
                    ok, new_id, err = crear_socio(
                        rut=rut.strip(),
                        nombre=nombre.strip(),
                        apellido_p=apellido_p.strip(),
                        apellido_m=(apellido_m.strip() or None) if apellido_m else None,
                        fecha_nac=_to_iso(fecha_nac),
                        telefono=(telefono.strip() or None) if telefono else None,
                        direccion=(direccion.strip() or None) if direccion else None,
                    )
                    if ok:
                        st.success(f"✅ Socio {nombre} {apellido_p} registrado. ID {new_id}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ No se pudo registrar. Detalle: {err}")
                except Exception as e:
                    st.error(f"❌ Error inesperado al registrar: {e}")

    # ------------------------------------------------------------
    # TAB 3: BUSCAR / EDITAR / ELIMINAR
    # ------------------------------------------------------------
    with tab_buscar:
        st.subheader("Buscar socio por RUT")

        cleft, cright = st.columns([3, 1])
        with cleft:
            rut_buscar = st.text_input("Ingrese RUT", placeholder="12345678-9", label_visibility="collapsed")
        with cright:
            buscar_btn = st.button("🔍 Buscar", type="primary", width='stretch')

        if buscar_btn:
            # Busca en la base de datos
            if not rut_buscar:
                st.warning("⚠️ Ingrese un RUT antes de buscar")
            else:
                socio = buscar_socio_por_rut(rut_buscar.strip())
                if not socio:
                    st.error("❌ No se encontro ningun socio con ese RUT")
                    st.session_state["socio_encontrado"] = None
                else:
                    st.session_state["socio_encontrado"] = socio
                    st.success("✅ Socio encontrado")

        socio = st.session_state.get("socio_encontrado")

        # Si encuentra socio, muestra ficha completa y menu de acciones
        if socio:
            with st.container(border=True):

                # Datos principales
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Nombre Completo:**  \n{socio['nombre']} {socio['apellido_p']} {socio.get('apellido_m') or ''}")
                    st.markdown(f"**RUT:**  \n{socio['RUT']}")
                    st.markdown(f"**Telefono:**  \n{socio.get('telefono') or 'No registrado'}")
                with c2:
                    st.markdown(f"**Fecha Nacimiento:**  \n{socio['fecha_nac']}")
                    st.markdown(f"**Direccion:**  \n{socio.get('direccion') or 'No registrada'}")

                st.markdown("---")
                st.subheader("✏️ Editar datos del socio")

                # Formulario de edicion
                with st.form(f"form_edit_{socio['id_socio']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        rut_n = st.text_input("RUT", value=socio["RUT"])
                        nom_n = st.text_input("Nombre", value=socio["nombre"])
                        ap_p_n = st.text_input("Apellido Paterno", value=socio["apellido_p"])
                    with c2:
                        ap_m_n = st.text_input("Apellido Materno", value=socio.get("apellido_m") or "")
                        fnac_n = st.date_input(
                            "Fecha de Nacimiento",
                            value=datetime.strptime(socio["fecha_nac"], "%Y-%m-%d").date(),
                            min_value=date(1920, 1, 1),
                            max_value=date.today()
                        )

                    t1, t2 = st.columns(2)
                    with t1:
                        tel_n = st.text_input("Telefono", value=socio.get("telefono") or "")
                    with t2:
                        dir_n = st.text_area("Direccion", value=socio.get("direccion") or "", height=80)

                    save = st.form_submit_button("💾 Guardar cambios", type="primary", width='stretch')

                # Guarda edicion
                if save:
                    ok, rows, err = actualizar_socio(
                        id_socio=socio["id_socio"],
                        rut=rut_n.strip(),
                        nombre=nom_n.strip(),
                        apellido_p=ap_p_n.strip(),
                        apellido_m=(ap_m_n.strip() or None),
                        fecha_nac=_to_iso(fnac_n),
                        telefono=(tel_n.strip() or None),
                        direccion=(dir_n.strip() or None)
                    )
                    if ok and rows > 0:
                        st.success("✅ Cambios guardados")
                        st.session_state["socio_encontrado"] = None
                        st.rerun()
                    else:
                        st.error(f"❌ No se pudo actualizar: {err or 'sin cambios'}")

                st.markdown("---")
                st.subheader("🗑️ Eliminar socio")

                confirmar = st.checkbox("Si, eliminar este socio")

                if st.button("Eliminar ahora", type="secondary", disabled=not confirmar):
                    ok, rows, err = eliminar_socio(socio["id_socio"])
                    if ok and rows > 0:
                        st.success("🧹 Socio eliminado")
                        st.session_state["socio_encontrado"] = None
                        st.rerun()
                    else:
                        st.error(f"❌ No se pudo eliminar: {err or 'verifique dependencias'}")