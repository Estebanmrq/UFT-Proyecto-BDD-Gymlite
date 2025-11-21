# views/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict
from database import (
    count_socios_activos, count_entrenadores_activos, count_reservas_hoy,
    count_clases_hoy, ingresos_mes_actual, get_all_proximas_clases,
    get_clases_proximas_con_alertas, get_historial_pagos, get_all_socios,
    get_all_clases, membresias_por_vencer,
    get_stats_last_7_days,
    current_db_path

)


# ========== Fonction para crear gráficos ==========

def create_clases_by_type_chart():
    try:
        clases = get_all_proximas_clases() or []

        if not clases:
            # st.warning("No hay datos de proxima clases disponibles.")
            return px.pie(title="Sin datos de clases")
        else:
            type_counts = {}
            for clase in clases:
                tipo = clase.get('tipo_clase', 'No especificado')
                type_counts[tipo] = type_counts.get(tipo, 0) + 1

            df = pd.DataFrame({
                'Tipo': list(type_counts.keys()),
                'Total': list(type_counts.values())
            })

        fig = px.pie(
            df,
            values='Total',
            names='Tipo',
            title="Distribución de tipos de clases",
            color_discrete_sequence=px.colors.qualitative.Dark2_r
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig

    except Exception as e:
        st.error(f"Error creación gráfico tipos: {e}")
        return px.pie()


def create_payment_methods_chart():
    try:
        pagos = get_historial_pagos(100) or []

        if not pagos:
            return px.bar(title="Sin datos de pagos")
        else:
            method_totals = {}
            for pago in pagos:
                metodo = pago.get('metodo_pago', 'No especificado')
                monto = pago.get('monto', 0)
                method_totals[metodo] = method_totals.get(metodo, 0) + monto

            df = pd.DataFrame({
                'Metodo': list(method_totals.keys()),
                'Monto': list(method_totals.values())
            })

        fig = px.bar(
            df,
            x='Metodo',
            y='Monto',
            title="Ingresos por método de pago",
            color='Metodo',
            color_discrete_sequence=px.colors.qualitative.Dark2_r
        )
        fig.update_layout(xaxis_title="Metodo de pago", yaxis_title="Monto Total ($)")
        return fig

    except Exception as e:
        st.error(f"Error creación gráfico pagos: {e}")
        return px.bar()


def create_reservations_trend_chart():
    try:
        # OBTENER DATOS REALES SQL DESDE DATABASE.PY
        stats = get_stats_last_7_days()

        df = pd.DataFrame({
            'Fecha': stats['fechas'],
            'Reservacion': stats['reservas'],
            'Clase': stats['clases']
        })

        fig = go.Figure()

        # Línea de Reservas
        fig.add_trace(go.Scatter(
            x=df['Fecha'],
            y=df['Reservacion'],
            mode='lines+markers',
            name='Reservas Reales',
            line=dict(color='#A6761D', width=3),
            marker=dict(size=8)
        ))

        # Línea de Clases
        fig.add_trace(go.Scatter(
            x=df['Fecha'],
            y=df['Clase'],
            mode='lines+markers',
            name='Clases Programadas',
            line=dict(color='#666666', width=3),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title="Evolución Real (Últimos 7 días)",
            xaxis_title="Fecha",
            yaxis_title="Cantidad",
            hovermode='x unified'
        )

        return fig

    except Exception as e:
        st.error(f"Error creación gráfico evolución: {e}")
        return go.Figure()


# ========== FUNCIONES DE VISUALIZACIÓN DE LA SECCIÓN ==========

def render_alerts_section():
    try:
        alertas_clases = get_clases_proximas_con_alertas() or []

        if alertas_clases:
            st.error(f"🚨 {len(alertas_clases)} cursos con pocos cupos")
            for alerta in alertas_clases[:3]:
                cupos = alerta.get('cupos_disponibles', 0)
                st.caption(f"• {alerta.get('nombre', 'Clase')} - {cupos} cupos disponibles")
        else:
            st.success("✅ Ninguna clase con cupos críticos")

        miembros_expiran = membresias_por_vencer(7) or []
        if miembros_expiran:
            st.warning(f"🔔 {len(miembros_expiran)} suscripciones caducan en 7 días")

        clases = get_all_proximas_clases() or []
        if clases:
            total_cupos = sum(c.get('cupo_max', 0) for c in clases)
            cupos_ocupados = sum((c.get('cupo_max', 0) - c.get('cupos_disponibles', 0)) for c in clases)
            if total_cupos > 0:
                ocupacion = (cupos_ocupados / total_cupos) * 100
                st.metric("📊 Tasa de ocupación", f"{ocupacion:.1f}%")

    except Exception as e:
        st.error(f"Error carga alertas: {e}")


def render_quick_stats():
    try:
        entrenadores = count_entrenadores_activos()
        socios = count_socios_activos()
        clases_proximas = len(get_all_proximas_clases() or [])

        col1, col2 = st.columns(2)

        with col1:
            st.metric("👨‍🏫 Entrenadores", entrenadores)
            st.metric("📚 Clases prox.", clases_proximas)

        with col2:
            st.metric("👥 Socios", socios)
            # st.metric("🏪 Índice de crecimiento", "+12%", delta="3 membres") # Eliminado por ser dato falso

    except Exception as e:
        st.error(f"Error carga estadísticas: {e}")


def render_active_members_table():
    try:
        socios = get_all_socios() or []

        if socios:
            table_data = []
            for socio in socios[:10]:
                table_data.append({
                    "ID": socio.get('id_socio', '—'),
                    "Nombre": f"{socio.get('nombre', '')} {socio.get('apellido_p', '')}",
                    "Telefono": socio.get('telefono', '—'),
                    "RUT": socio.get('RUT', '—')
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No hay socios activos")

    except Exception as e:
        st.error(f"Error carga socios: {e}")


def render_recent_payments_table():
    try:
        pagos = get_historial_pagos(10) or []

        if pagos:
            table_data = []
            for pago in pagos:
                table_data.append({
                    "ID": pago.get('id_pago', '—'),
                    "Membro": pago.get('nombre_socio', '—'),
                    "Monto": f"${pago.get('monto', 0):,.0f}",
                    "Metodo": pago.get('metodo_pago', '—'),
                    "Fecha": pago.get('fecha_pago', '—'),
                    "Estado": pago.get('estado_pago', '—')
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No hay pagos recientes")

    except Exception as e:
        st.error(f"Error carga pagos: {e}")


def render():
    col1, col2 = st.columns([5, 1])

    with col1:
        st.title("📊 Dashboard - GymLite")
        st.caption("Vista general completa del gimnasio")

    with col2:
        if st.button("🔄 Actualizar Datos", width="stretch"):
            st.rerun()

        try:
            with open(current_db_path(), "rb") as fp:
                st.download_button(
                    label="💾 Descargar Respaldo",
                    data=fp,
                    file_name="GymLite_backup.db",
                    mime="application/x-sqlite3",
                    help="Descarga una copia completa de la base de datos (RNF-04)"
                )
        except Exception:
            st.warning("No se pudo generar el respaldo.")

    st.markdown("---")

    try:

        socios_activos = count_socios_activos()
        clases_hoy = count_clases_hoy()
        entrenadores_activos = count_entrenadores_activos()
        reservas_hoy = count_reservas_hoy()
        ingresos_mes = ingresos_mes_actual()

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "👥 Socios Activos",
                socios_activos if socios_activos is not None else "—",
                help="Total de socios con membresía activa"
            )

        with col2:
            st.metric(
                "🏃 Clases Hoy",
                clases_hoy if clases_hoy is not None else "—",
                help="Clases programadas para hoy"
            )

        with col3:
            st.metric(
                "👨‍🏫 Entrenadores",
                entrenadores_activos if entrenadores_activos is not None else "—",
                help="Entrenadores activos en el sistema"
            )

        with col4:
            st.metric(
                "📅 Reservas Hoy",
                reservas_hoy if reservas_hoy is not None else "—",
                help="Reservas confirmadas para hoy"
            )

        with col5:
            st.metric(
                "💰 Ingresos Mes",
                f"${ingresos_mes:,.0f}" if ingresos_mes is not None else "—",
                help="Ingresos totales del mes actual"
            )

    except Exception as e:
        st.error(f"❌ Error al cargar métricas: {e}")

    st.markdown("---")

    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("📅 Próximas Clases")
        try:
            clases = get_all_proximas_clases(8)

            if clases:
                data = []
                for clase in clases:
                    fecha_hora = clase.get('fecha_hora', '')
                    if fecha_hora:
                        try:
                            dt = datetime.fromisoformat(fecha_hora.replace('Z', '+00:00'))
                            fecha_formateada = dt.strftime("%d/%m/%Y %H:%M")
                        except:
                            fecha_formateada = str(fecha_hora)[:16]
                    else:
                        fecha_formateada = "—"

                    cupos_disponibles = clase.get('cupos_disponibles', 0)
                    cupo_max = clase.get('cupo_max', 0)

                    data.append({
                        "Clase": clase.get('nombre', '—'),
                        "Tipo": clase.get('tipo_clase', '—'),
                        "Fecha/Hora": fecha_formateada,
                        "Entrenador": clase.get('entrenador', '—'),
                        "Cupos": f"{cupos_disponibles}/{cupo_max}",
                        "Disponibilidad": cupos_disponibles
                    })

                df = pd.DataFrame(data)

                styled_df = df.style.apply(
                    lambda x: ['background-color: #ffcccc' if x['Disponibilidad'] == 0 else
                               'background-color: #fff3cd' if x['Disponibilidad'] <= 3 else
                               '' for _ in x],
                    axis=1
                )

                st.dataframe(
                    df.drop('Disponibilidad', axis=1),
                    width="stretch",
                    hide_index=True,
                    height=min(400, len(data) * 35 + 38)
                )

                clases_llenas = sum(1 for c in clases if c.get('cupos_disponibles', 0) <= 0)
                clases_con_pocos_cupos = sum(1 for c in clases if 0 < c.get('cupos_disponibles', 0) <= 3)

                st.caption(f"📊 {len(clases)} clases programadas • "
                           f"🚨 {clases_llenas} sin cupos • "
                           f"🔔 {clases_con_pocos_cupos} con pocos cupos")

            else:
                st.info("📭 No hay clases programadas.")
                st.caption("Las próximas clases aparecerán aquí automáticamente.")

            # ========== SECTION GRAFICOS ==========
            st.subheader("📈 Visualizaciones")

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                try:
                    fig_tipos = create_clases_by_type_chart()
                    st.plotly_chart(fig_tipos, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Error al cargar gráfico de tipos: {e}")

            with chart_col2:
                try:
                    fig_pagos = create_payment_methods_chart()
                    st.plotly_chart(fig_pagos, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Error al cargar gráfico de pagos: {e}")

            try:
                fig_evolucion = create_reservations_trend_chart()
                st.plotly_chart(fig_evolucion, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error al cargar gráfico de evolución: {e}")
                st.info("📈 Gráfico de tendencias no disponible")

        except Exception as e:
            st.error(f"❌ Error al cargar clases: {e}")
            st.info("💡 Intenta recargar la página o verificar la conexión con la base de datos.")

    with col_der:
        st.subheader("⚠️ Alertas y Estadísticas")

        try:
            # Alertes améliorées
            alertas = get_clases_proximas_con_alertas() or []
            alertas_urgentes = [a for a in alertas if a.get('cupos_disponibles', 0) <= 0]
            alertas_proximas = [a for a in alertas if 0 < a.get('cupos_disponibles', 0) <= 3]

            # Alertes de cours
            if alertas_urgentes:
                with st.expander(f"🚨 {len(alertas_urgentes)} Clases Sin Cupos", expanded=True):
                    for alerta in alertas_urgentes[:5]:
                        st.caption(f"• {alerta.get('nombre', 'Clase')}")

            if alertas_proximas:
                with st.expander(f"🔔 {len(alertas_proximas)} Clases Con Pocos Cupos", expanded=True):
                    for alerta in alertas_proximas[:5]:
                        cupos = alerta.get('cupos_disponibles', 0)
                        st.caption(f"• {alerta.get('nombre', 'Clase')} - {cupos} cupo(s)")

            if not alertas_urgentes and not alertas_proximas:
                st.success("✅ Sin alertas críticas")
                st.caption("Todas las clases tienen cupos disponibles")

            try:
                membresias_expirando = membresias_por_vencer(7) or []
                if membresias_expirando:
                    with st.expander(f"📅 {len(membresias_expirando)} Membresías por Vencer", expanded=True):
                        for membresia in membresias_expirando[:3]:
                            nombre = membresia.get('nombre_socio', 'Socio')
                            dias = membresia.get('dias_restantes', 0)
                            st.caption(f"• {nombre} - {dias} día(s)")
            except Exception as e:
                st.caption("💡 Información de membresías no disponible")

            st.markdown("---")
            st.subheader("📈 Resumen Rápido")

            if clases:
                clases_proximas_7dias = len(clases)
                cupos_totales = sum(c.get('cupo_max', 0) for c in clases)
                cupos_ocupados = sum((c.get('cupo_max', 0) - c.get('cupos_disponibles', 0)) for c in clases)

                col_stat1, col_stat2 = st.columns(2)

                with col_stat1:
                    if cupos_totales > 0:
                        ocupacion_porcentaje = (cupos_ocupados / cupos_totales) * 100
                        st.metric("📊 Ocupación", f"{ocupacion_porcentaje:.1f}%")
                    else:
                        st.metric("📊 Ocupación", "0%")

                    st.metric("🗓️ Próximas", clases_proximas_7dias)

                with col_stat2:
                    tipos_unicos = len(set(c.get('tipo_clase', '') for c in clases))
                    entrenadores_unicos = len(set(c.get('entrenador', '') for c in clases))

                    st.metric("🎯 Tipos", tipos_unicos)
                    st.metric("👨‍🏫 Profesores", entrenadores_unicos)

            else:
                col_stat1, col_stat2 = st.columns(2)
                with col_stat1:
                    st.metric("📊 Ocupación", "0%")
                    st.metric("🗓️ Próximas", 0)
                with col_stat2:
                    st.metric("🎯 Tipos", 0)
                    st.metric("👨‍🏫 Profesores", 0)

            # ELIMINADO EL GRÁFICO HARDCODED AQUÍ

        except Exception as e:
            st.error(f"❌ Error en alertas: {e}")
            st.info("💡 Las funciones de alerta no están disponibles temporalmente")

    # ========== TABLAS DE DATOS DETALLADOS ==========
    st.markdown("---")
    st.subheader("📋 Datos Detallados")

    tab1, tab2, tab3 = st.tabs(["🎯 Últimos Pagos", "👥 Socios Recientes", "📊 Estadísticas"])

    with tab1:
        try:
            render_recent_payments_table()
        except Exception as e:
            st.error(f"❌ Error al cargar pagos: {e}")
            st.info("💳 No se pudieron cargar los datos de pagos")

    with tab2:
        try:
            render_active_members_table()
        except Exception as e:
            st.error(f"❌ Error al cargar socios: {e}")
            st.info("👥 No se pudieron cargar los datos de socios")

    with tab3:
        try:
            render_quick_stats()
        except Exception as e:
            st.error(f"❌ Error al cargar estadísticas: {e}")
            st.info("📈 No se pudieron cargar las estadísticas detalladas")