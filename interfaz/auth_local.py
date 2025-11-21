# auth_local.py — Autenticacion local (SQLite + bcrypt) para Streamlit
import sqlite3
import time
from typing import Optional
import bcrypt

DB_PATH = "users.db"   # Archivo de la base de datos dentro del proyecto

# Esquema de la tabla principal de usuarios.
# Se crean campos basicos: usuario, contrasena en hash, rol y estado.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',   -- 'admin' | 'editor' | 'viewer'
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL
);
"""

def _conn():
    # Conexion simple para no repetir codigo
    return sqlite3.connect(DB_PATH)

def ensure_db(seed_admin: bool = True):
    with _conn() as con:
        con.execute(SCHEMA)

        # Si la base esta vacia, se crea un usuario admin por defecto.
        # Esto evita que la app quede sin forma de ingresar la primera vez.
        if seed_admin:
            c = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if c == 0:
                create_user("admin", "Admin1234!", role="admin")

def create_user(username: str, password: str, role: str = "viewer") -> int:
    # Se genera el hash de la contrasena usando bcrypt
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    with _conn() as con:
        # Insercion del usuario en la base
        cur = con.execute(
            "INSERT INTO users (username, password_hash, role, is_active, created_at) VALUES (?,?,?,?,?)",
            (username, pw_hash, role, 1, int(time.time()))
        )
        return cur.lastrowid

def get_user(username: str) -> Optional[tuple]:
    # Obtiene la fila del usuario por nombre
    with _conn() as con:
        row = con.execute(
            "SELECT id, username, password_hash, role, is_active FROM users WHERE username=?",
            (username,)
        ).fetchone()
    return row

def verify_user(username: str, password: str) -> Optional[dict]:
    # Validacion de login: recupera al usuario y compara hashes
    row = get_user(username)
    if not row:
        return None

    uid, uname, pw_hash, role, is_active = row

    # Usuario desactivado -> no entra
    if not is_active:
        return None

    # bcrypt compara el password ingresado con el hash guardado
    if bcrypt.checkpw(password.encode("utf-8"), pw_hash):
        return {"id": uid, "username": uname, "role": role}

    return None

def change_password(username: str, new_password: str) -> bool:
    # Actualiza la contrasena con un nuevo hash
    pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    with _conn() as con:
        res = con.execute(
            "UPDATE users SET password_hash=? WHERE username=?",
            (pw_hash, username)
        )
        return res.rowcount > 0

def set_role(username: str, role: str) -> bool:
    # Actualiza el rol del usuario (admin/editor/viewer)
    with _conn() as con:
        res = con.execute("UPDATE users SET role=? WHERE username=?", (role, username))
        return res.rowcount > 0

# Sistema simple de niveles de permisos.
# Cada rol tiene un nivel numerico para comparar acceso.
_ROLE_ORDER = {"viewer": 0, "editor": 1, "admin": 2}

def has_role(user_role: str, allowed=("viewer","editor","admin")) -> bool:
    # Verifica si el rol del usuario tiene nivel suficiente para entrar.
    return _ROLE_ORDER.get(user_role, -1) >= min(_ROLE_ORDER.get(r, 99) for r in allowed)
