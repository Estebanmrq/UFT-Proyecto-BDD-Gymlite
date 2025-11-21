# app.py — GymLite
import streamlit as st

# Configuracion antes de cualquier otro st.*
st.set_page_config(page_title="GymLite", page_icon="🏋️", layout="wide")

# Imports de dominio
from auth_local import ensure_db, verify_user, create_user, change_password, has_role

from database import ensure_full_schema, init_db_data
try:
    # Intento de import desde carpeta 'views' 
    from views import dashboard, socios, clases, pagos
except Exception:
    # En algunos setups las paginas pueden estar en 'pages'
    from pages import dashboard, socios, clases, pagos

import navbar

# Asegura que la DB y usuario admin existan
ensure_db(seed_admin=True)

# Asegura esquema y datos iniciales de la base
ensure_full_schema()
init_db_data()

# Estado de autenticacion en session_state
if "auth" not in st.session_state:
    st.session_state.auth = {"ok": False, "username": None, "role": None}


ENFORCE_RBAC = False  

# ==============================
#   Estilos globales
# ==============================
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }
main .block-container {
    padding-top: 0.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 95%;
}
</style>
""", unsafe_allow_html=True)


# ==============================
#   Login pantalla completa
# ==============================
def full_screen_login():
    # Estilos y layout para la pantalla de login 
    st.markdown("""
    <style>
    .stApp { background-color: #0f1116; }
    section.main > div {
        max-width: 520px;
        margin: auto;
        padding-top: 12vh;
        text-align: center;
    }
    h1.title {
        font-size: 2.6rem; color: #fff; font-weight: 800; margin-bottom: .2rem;
    }
    .subtle { color: #9aa4bf; margin: .2rem 0 1rem 0; }
    .stTextInput > div > div > input,
    .stPassword > div > div > input {
        background: #151923 !important; color: #fff !important;
        border: 1px solid #242a36 !important; border-radius: 10px !important;
    }
    button[kind="primary"] {
        background: #ff4b4b !important; border-radius: 10px !important; font-weight: 700 !important;
    }
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='title'>🏋️ GymLite</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtle'>Inicia sesiÃ³n para continuar</p>", unsafe_allow_html=True) 

    modo = st.radio("Modo:", ["Iniciar sesión", "Registrar usuario"], horizontal=True, label_visibility="collapsed")

    if modo == "Iniciar sesión":
        # Formulario de login
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            ok = st.form_submit_button("🔑 Entrar", width='stretch')
        if ok:
            user = verify_user(u, p)
            if user:
                # Guarda info minima de sesion
                st.session_state.auth = {"ok": True, "username": user["username"], "role": user["role"]}
                st.session_state["TopNav__active"] = "Dashboard"
                st.success(f"Bienvenido, {user['username']}")
                st.rerun()
            else:
                st.error("Usuario o contrasena incorrectos")

    else:
        # Registro basico de usuario
        with st.form("register_form"):
            u = st.text_input("Crea tu usuario")
            p1 = st.text_input("Contraseña", type="password")
            p2 = st.text_input("Repite contraseña", type="password")
            ok = st.form_submit_button("🆕 Registrar", width='stretch')
        if ok:
            if len(u) < 3:
                st.warning("El usuario debe tener al menos 3 caracteres.")
            elif len(p1) < 8:
                st.warning("La contrasena debe tener al menos 8 caracteres.")
            elif p1 != p2:
                st.warning("Las contrasenas no coinciden.")
            else:
                try:
                    create_user(u, p1, role="viewer")
                    st.success("✅ Usuario registrado. Ahora inicia sesiÃ³n.")
                except Exception as e:
                    # Mostrar error 
                    st.error(f"Error al registrar: {e}")


# ==============================
#   Guard
# ==============================
def guard(allowed_roles=("viewer", "editor", "admin")):
    # Protege rutas; si no hay sesion, muestra login y corta ejecucion
    if not st.session_state.auth["ok"]:
        full_screen_login()
        st.stop()

    if ENFORCE_RBAC and not has_role(st.session_state.auth["role"], allowed_roles):
        st.error("🚫 No tienes permisos para acceder a esta seccion.")
        st.stop()


# ==============================
#   Barra superior de sesion
# ==============================
def session_bar():
    # Muestra usuario y rol actuales y boton de cerrar sesion
    user = st.session_state.auth.get("username") or "invitado"
    role = st.session_state.auth.get("role") or "viewer"

    st.markdown("""
    <style>
    .sessbar { display:flex; justify-content:flex-end; gap:12px; align-items:center; margin:.25rem 0 1rem 0; }
    .chip {
        background:#151923; color:#c7cfdd; padding:6px 12px; border-radius:999px;
        border:1px solid #242a36; font-size:.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([6, 2])
    with c1:
        st.empty()
    with c2:
        st.markdown(
            f"<div class='sessbar'><div class='chip'>👤 {user}</div><div class='chip'>🛡️ {role}</div></div>",
            unsafe_allow_html=True
        )
        if st.button("🚪 Cerrar sesiÃ³n", width='stretch'):
            # Resetea autenticacion y recarga la app
            st.session_state.auth = {"ok": False, "username": None, "role": None}
            st.rerun()


# ==============================
#   Main
# ==============================
def main():
    # Exige sesion
    if not st.session_state.auth["ok"]:
        full_screen_login()
        st.stop()

    # Muestra barra de sesion arriba
    session_bar()

    # pagina -> funcion render y roles permitidos
    PAGES = {
        "Dashboard": {"fn": dashboard.render, "roles": ("viewer", "editor", "admin")},
        "Socios":    {"fn": socios.render,    "roles": ("editor", "admin")},
        "Clases":    {"fn": clases.render,    "roles": ("viewer", "editor", "admin")},
        "Pagos":     {"fn": pagos.render,     "roles": ("admin",)},
    }

    selected = navbar.top_nav(options=list(PAGES.keys()), default_index=0, key="TopNav")

    # Verifica permisos para la pagina seleccionada
    guard(allowed_roles=PAGES[selected]["roles"])

    st.title("GymLite")
    # Llama la funcion render de la pagina
    PAGES[selected]["fn"]()


if __name__ == "__main__":
    main()
