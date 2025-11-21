# views/pagos.py — Registrar pagos y gestionar suscripciones 
import streamlit as st
import pandas as pd
from datetime import date
from database import (
    # pagos / historial
    get_historial_pagos, registrar_pago,
    # socios
    get_all_socios,
    # planes / suscripciones
    get_planes, crear_suscripcion,
    get_suscripcion_activa_por_socio, get_suscripciones_por_socio,
)

def _fmt_money(v):
    try:
        return f"${float(v):,.0f}".replace(",", ".")
    except Exception:
        return str(v)

def render():
    st.title("💳 Pagos")
    st.caption("Registrar pagos asociados a la suscripcion activa del socio")

    tab1, tab2 = st.tabs(["➕ Registrar Pago", "📋 Historial y Reportes"])

    # ============================================================
    # TAB 1: REGISTRAR PAGO con gestion de suscripcion
    # ============================================================
    with tab1:
        st.subheader("Selecciona socio y verifica su suscripcion")
        socios = get_all_socios()
        if not socios:
            st.info("No hay socios registrados.")
            return

        # Construye opciones para el selectbox
        opciones = {
            f"{s['id_socio']} — {s['nombre']} {s['apellido_p']} ({s['RUT']})": s
            for s in socios
        }
        elegido = st.selectbox("Socio", list(opciones.keys()), index=0)
        socio = opciones[elegido]

        # Obtiene suscripcion activa del socio
        activa = get_suscripcion_activa_por_socio(socio["id_socio"])

        if not activa:
            st.warning("Este socio no tiene suscripcion activa.")
            with st.expander("➕ Crear suscripcion ahora", expanded=True):
                planes = get_planes()
                if not planes:
                    st.error("No hay planes en la base de datos. Carga la semilla de planes primero.")
                else:
                    mapa = {
                        f"{p['nombre_plan']} ({p['duracion_meses']} mes/es) — {_fmt_money(p['precio'])}": p
                        for p in planes
                    }
                    label = st.selectbox("Plan", list(mapa.keys()))
                    plan = mapa[label]
                    inicio = st.text_input("Fecha inicio (YYYY-MM-DD)", value=str(date.today()))

                    if st.button("Crear suscripcion", type="primary"):
                        ok, sid, err = crear_suscripcion(socio["id_socio"], plan["id_plan"], inicio)
                        if ok:
                            st.success(f"Suscripcion creada ID {sid}.")
                            st.rerun()
                        else:
                            st.error(f"No se pudo crear la suscripcion. {err or ''}")
        else:
            # Muestra resumen de la suscripcion activa
            st.success(
                f"Suscripcion activa #{activa['id_suscripcion']} • "
                f"{activa['nombre_plan']} • {activa['fecha_inicio']} → {activa['fecha_fin']} "
                f"{activa['estado_sus']} • Precio: {_fmt_money(activa.get('precio', 0))}"
            )

            st.markdown("### Registrar pago")
            # Formulario de registro de pago
            with st.form("form_registrar_pago"):
                monto = st.number_input(
                    "Monto *",
                    min_value=0.0,
                    value=float(activa.get("precio") or 0.0),
                    step=1000.0,
                )
                metodo = st.selectbox("Método de Pago *", ["efectivo", "transferencia", "tarjeta", "webpay"])
                comprobante = st.text_input("N° Comprobante (opcional)")
                submitted = st.form_submit_button("💾 Guardar pago", type="primary", width='stretch')

            if submitted:
                ok, new_id, err = registrar_pago(
                    id_suscripcion=int(activa["id_suscripcion"]),
                    monto=float(monto),
                    metodo=metodo,
                    comprobante=(comprobante or None),
                )
                if ok:
                    st.success(f"✅ Pago registrado ID {new_id}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ No se pudo registrar el pago. Detalle: {err or ''}")

            # Muestra suscripciones del socio
            with st.expander("🪪 Suscripciones del socio historico"):
                suscs = get_suscripciones_por_socio(socio["id_socio"])
                if not suscs:
                    st.info("Este socio aun no tiene suscripciones.")
                else:
                    for s in suscs:
                        st.write(
                            f"• {s['nombre_plan']} — {s['fecha_inicio']} → {s['fecha_fin']} "
                            f"{s['estado_sus']}  |  {_fmt_money(s['precio'])}"
                        )

    # ============================================================
    # TAB 2: HISTORIAL FILTROS KPIS
    # ============================================================
    with tab2:
        st.subheader("Historial de pagos")

        c1, c2, c3 = st.columns(3)
        with c1:
            limite = st.selectbox("Mostrar ultimos:", [50, 100, 200, 500], index=1)
        with c2:
            filtro_metodo = st.multiselect(
                "Filtrar por metodo",
                ["efectivo", "transferencia", "tarjeta", "webpay"],
                default=[]
            )
        with c3:
            rango = st.date_input(
                "Rango de fechas opcional",
                value=(date(date.today().year, 1, 1), date.today()),
                help="Filtra por fecha de pago, incluye extremos. Deja vacio si no quieres filtrar.",
            )

        try:
            pagos = get_historial_pagos(limit=limite)
            if not pagos:
                st.info("📭 No hay pagos registrados.")
                return

            df = pd.DataFrame(pagos)
            if "fecha_pago" in df.columns:
                df["fecha_pago"] = pd.to_datetime(df["fecha_pago"], errors="coerce")
            if "monto" in df.columns:
                df["monto"] = pd.to_numeric(df["monto"], errors="coerce")

            # Aplica filtro por metodo
            if filtro_metodo and "metodo_pago" in df.columns:
                df = df[df["metodo_pago"].isin(filtro_metodo)]

            # Aplica filtro por rango de fechas
            if isinstance(rango, tuple) and len(rango) == 2 and "fecha_pago" in df.columns:
                d1, d2 = rango
                df = df[(df["fecha_pago"].dt.date >= d1) & (df["fecha_pago"].dt.date <= d2)]

            if "fecha_pago" in df.columns:
                df = df.sort_values("fecha_pago", ascending=False)

            df_show = df.copy()
            if "monto" in df_show.columns:
                df_show["monto"] = df_show["monto"].map(_fmt_money)
            st.dataframe(df_show, width='stretch', hide_index=True)

            
            st.markdown("---")
            st.subheader("📈 Estadisticas")
            k1, k2, k3, k4 = st.columns(4)
            total_pagos = len(df)
            total_monto = df["monto"].sum() if "monto" in df.columns else 0
            promedio = df["monto"].mean() if "monto" in df.columns and len(df) else 0
            metodo_top = df["metodo_pago"].mode()[0] if "metodo_pago" in df.columns and len(df) else "N/A"
            k1.metric("Total pagos", total_pagos)
            k2.metric("Monto total", _fmt_money(total_monto))
            k3.metric("Promedio", _fmt_money(promedio))
            k4.metric("Metodo mas usado", metodo_top)

            # Desglose por metodo de pago
            st.markdown("---")
            st.subheader("💳 Desglose por metodo de pago")
            if "metodo_pago" in df.columns and "monto" in df.columns and len(df):
                desglose = (
                    df.groupby("metodo_pago")["monto"]
                    .agg(total="sum", cantidad="count")
                    .reset_index()
                    .rename(columns={"metodo_pago": "Metodo", "total": "Total", "cantidad": "Cantidad"})
                )
                cta, ch = st.columns([1, 2])
                with cta:
                    show = desglose.copy()
                    show["Total"] = show["Total"].map(_fmt_money)
                    st.dataframe(show, width='stretch', hide_index=True)
                with ch:
                    # Grafico rapido de barras por total por metodo
                    st.bar_chart(desglose.set_index("Metodo")["Total"])
        except Exception as e:
            st.error(f"❌ Error al cargar historial de pagos: {e}")
            st.exception(e)
