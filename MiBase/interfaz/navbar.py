# navbar.py — Barra de navegación superior
from __future__ import annotations
import streamlit as st

# Se intenta importar el componente 'option_menu' para un menú más visual.
# Si no está disponible, el código realiza un fallback a un control nativo de Streamlit.
try:
    from streamlit_option_menu import option_menu
    HAS_OPTION_MENU = True
except Exception:
    HAS_OPTION_MENU = False


def top_nav(
    options: list[str] | tuple[str, ...] = ("Dashboard", "Socios", "Clases", "Pagos"),
    icons: list[str] | tuple[str, ...] = ("speedometer2", "people-fill", "calendar-event", "cash-stack"),
    default_index: int = 0,
    key: str = "TopNav",
) -> str:
    """
    Renderiza un menú superior horizontal y devuelve el nombre de la página seleccionada.
    - Si está disponible `streamlit-option-menu`, lo usa (look & feel pro).
    - Si NO, hace fallback a `st.radio` horizontal controlado.
    """
    
    # Normalización de parámetros de entrada y control de valores por defecto
    opts = list(options) if options else ["Dashboard"]
    icons = list(icons)[: len(opts)]
    default_index = max(0, min(default_index, len(opts) - 1))

    # Se obtiene la última opción seleccionada desde el estado de sesión 
    active_name = st.session_state.get(f"{key}__active", opts[default_index])
    if active_name not in opts:
        active_name = opts[default_index]
    idx_from_state = opts.index(active_name)

    with st.container():

        if HAS_OPTION_MENU:
            selected = option_menu(
                menu_title=None,
                options=opts,
                icons=icons,
                menu_icon="cast",
                default_index=idx_from_state,
                orientation="horizontal",
                styles={
                    # Personalización del estilo general del contenedor y enlaces
                    "container": {"padding": "0!important", "background-color": "rgba(0,0,0,0)"},
                    "icon": {"color": "#FF4B4B", "font-size": "20px"},
                    "nav-link": {
                        "font-size": "16px",
                        "text-align": "center",
                        "margin": "0px",
                        "--hover-color": "rgba(255,255,255,0.06)",
                    },
                    "nav-link-selected": {"background-color": "#FF4B4B", "color": "white"},
                },
                key=key,  # Clave única para mantener el estado dentro de Streamlit
            )


            st.session_state[f"{key}__active"] = selected
            return selected


        selected = st.radio(
            "Navegación",
            opts,
            index=idx_from_state,
            horizontal=True,
            key=f"{key}__radio",
        )

        st.session_state[f"{key}__active"] = selected
        return selected
