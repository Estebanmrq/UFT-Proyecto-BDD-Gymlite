# database.py — Capa de acceso a datos para GymLite 

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# ============================================================
# RESOLUCIÓN DE RUTA A LA DB
# ============================================================

# Se intenta encontrar la DB automáticamente en la carpeta del proyecto:
# - "GymLite" (sin extensión) o
# - "GymLite.db"
def _auto_resolve_db_path() -> str:
    here = Path(__file__).resolve().parent
    candidatos = [
        here / "GymLite",       # sin extensión
        here / "GymLite.db",    # con extensión
    ]
    for p in candidatos:
        if p.exists():
            return p.as_posix()
    # Si no existe ninguna, por defecto se crea GymLite.db junto al archivo
    return (here / "GymLite.db").as_posix()

# Por defecto, se usa la resolución automática:
DB_PATH: str = _auto_resolve_db_path()

def current_db_path() -> str:
    """Devuelve la ruta absoluta actual de la DB."""
    return str(Path(DB_PATH).resolve())

def set_db_path(path: str | Path):
    """Sobrescribe la ruta a la DB en runtime (útil en app.py)."""
    global DB_PATH
    DB_PATH = Path(path).as_posix()

def get_conn() -> sqlite3.Connection:
    """
    Abre conexión SQLite con:
    - row_factory = sqlite3.Row (acceso por nombre de columna)
    - foreign_keys ON (integridad referencial)
    - autocommit (isolation_level=None) para simplificar
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

# Helper para listas de dicts
def _rows_to_dicts(rows) -> List[Dict]:
    return [dict(r) for r in rows] if rows is not None else None

# ============================================================
# ESQUEMA (opcional): inicialización completa si la DB está vacía
# ============================================================
def ensure_full_schema():
    """
    Crea todas las tablas y vistas si no existen.
    INCLUYE: Soft Delete en Socio y Triggers de seguridad.
    """
    ddl = """
    PRAGMA foreign_keys=ON;

    -- 1. TABLA SOCIO (MODIFICADA: Agregamos 'activo')
    CREATE TABLE IF NOT EXISTS Socio (
        id_socio INTEGER PRIMARY KEY AUTOINCREMENT,
        RUT VARCHAR(12) NOT NULL UNIQUE,
        nombre VARCHAR(50) NOT NULL,
        apellido_p VARCHAR(50) NOT NULL,
        apellido_m VARCHAR(50),
        fecha_nac DATE NOT NULL,
        telefono VARCHAR(12),
        direccion VARCHAR(100),
        activo INTEGER NOT NULL DEFAULT 1, -- 1=Activo, 0=Eliminado
        CHECK (LENGTH(RUT) >= 9)
    );

    -- 2. TABLAS ESTÁNDAR (Sin cambios mayores)
    CREATE TABLE IF NOT EXISTS Plan (
        id_plan INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_plan VARCHAR(50) NOT NULL UNIQUE,
        precio DECIMAL(10,2) NOT NULL,
        duracion_meses INTEGER NOT NULL,
        limite_clases INTEGER,
        beneficio TEXT,
        descripcion TEXT,
        CHECK (precio > 0),
        CHECK (duracion_meses > 0),
        CHECK (limite_clases IS NULL OR limite_clases > 0)
    );

    CREATE TABLE IF NOT EXISTS Suscripcion (
        id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_socio INTEGER NOT NULL,
        id_plan INTEGER NOT NULL,
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE NOT NULL,
        estado_sus VARCHAR(20) NOT NULL DEFAULT 'activa',
        FOREIGN KEY (id_socio) REFERENCES Socio(id_socio) ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (id_plan)  REFERENCES Plan(id_plan)  ON DELETE RESTRICT ON UPDATE CASCADE,
        CHECK (estado_sus IN ('activa','vencida','cancelada')),
        CHECK (fecha_fin > fecha_inicio)
    );

    CREATE TABLE IF NOT EXISTS Pago (
        id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
        id_suscripcion INTEGER NOT NULL,
        fecha_pago DATE NOT NULL DEFAULT (DATE('now')),
        monto DECIMAL(10,2) NOT NULL,
        metodo_pago VARCHAR(50) NOT NULL,
        estado_pago VARCHAR(20) NOT NULL DEFAULT 'completado',
        num_comprobante VARCHAR(50),
        FOREIGN KEY (id_suscripcion) REFERENCES Suscripcion(id_suscripcion) ON DELETE CASCADE ON UPDATE CASCADE,
        CHECK (monto > 0),
        CHECK (metodo_pago IN ('transferencia','webpay','tarjeta','efectivo')),
        CHECK (estado_pago IN ('pendiente','completado','rechazado'))
    );

    CREATE TABLE IF NOT EXISTS Tipo (
        id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre VARCHAR(50) NOT NULL UNIQUE,
        descripcion TEXT
    );

    CREATE TABLE IF NOT EXISTS Entrenador (
        id_entrenador INTEGER PRIMARY KEY AUTOINCREMENT,
        RUT VARCHAR(12) NOT NULL UNIQUE,
        nombre VARCHAR(50) NOT NULL,
        apellido VARCHAR(50) NOT NULL,
        telefono VARCHAR(12),
        fecha_nac DATE NOT NULL,
        especialidad VARCHAR(80) NOT NULL,
        CHECK (LENGTH(RUT) >= 9)
    );

    CREATE TABLE IF NOT EXISTS Clase (
        id_clase INTEGER PRIMARY KEY AUTOINCREMENT,
        id_entrenador INTEGER NOT NULL,
        id_tipo INTEGER NOT NULL,
        nombre VARCHAR(100) NOT NULL,
        descripcion TEXT,
        fecha_hora DATETIME NOT NULL,
        duracion_min INTEGER NOT NULL,
        cupo_max INTEGER NOT NULL,
        FOREIGN KEY (id_entrenador) REFERENCES Entrenador(id_entrenador) ON DELETE RESTRICT ON UPDATE CASCADE,
        FOREIGN KEY (id_tipo) REFERENCES Tipo(id_tipo) ON DELETE RESTRICT ON UPDATE CASCADE,
        CHECK (duracion_min > 0),
        CHECK (cupo_max > 0)
    );

    CREATE TABLE IF NOT EXISTS Reserva (
        id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
        id_socio INTEGER NOT NULL,
        id_clase INTEGER NOT NULL,
        fecha_reserva DATETIME NOT NULL DEFAULT (DATETIME('now')),
        estado_reserva VARCHAR(20) NOT NULL DEFAULT 'confirmada',
        asistio INTEGER DEFAULT 0,
        FOREIGN KEY (id_socio) REFERENCES Socio(id_socio) ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (id_clase) REFERENCES Clase(id_clase) ON DELETE CASCADE ON UPDATE CASCADE,
        CHECK (estado_reserva IN ('pendiente','confirmada','cancelada')),
        CHECK (asistio IN (0,1)),
        UNIQUE (id_socio, id_clase)
    );

    -- 3. VISTAS (Sin cambios)
    CREATE VIEW IF NOT EXISTS v_historial_pagos AS
    SELECT 
        pag.id_pago,
        s.RUT,
        s.nombre || ' ' || s.apellido_p AS nombre_socio,
        p.nombre_plan,
        pag.fecha_pago,
        pag.monto,
        pag.metodo_pago,
        pag.estado_pago
    FROM Pago pag
    JOIN Suscripcion sus ON pag.id_suscripcion = sus.id_suscripcion
    JOIN Socio s ON sus.id_socio = s.id_socio
    JOIN Plan  p ON sus.id_plan  = p.id_plan
    ORDER BY pag.fecha_pago DESC;

    CREATE VIEW IF NOT EXISTS v_socios_activos AS
    WITH ult AS (
      SELECT id_socio, MAX(fecha_fin) AS fecha_fin_max
      FROM Suscripcion
      GROUP BY id_socio
    )
    SELECT s.id_socio, s.RUT, s.nombre || ' ' || s.apellido_p AS nombre_completo,
           s.telefono, p.nombre_plan, sus.fecha_inicio, sus.fecha_fin, 'Vigente' AS vigencia
    FROM ult
    JOIN Suscripcion sus ON sus.id_socio = ult.id_socio AND sus.fecha_fin = ult.fecha_fin_max
    JOIN Socio s ON s.id_socio = sus.id_socio
    JOIN Plan  p ON p.id_plan = sus.id_plan
    WHERE sus.estado_sus='activa' AND DATE(sus.fecha_fin) >= DATE('now','localtime');

    -- =========================================
    -- 4. TRIGGERS (AQUI ESTA LA MAGIA)
    -- =========================================

    -- Trigger: Evitar sobrecupo (Race Condition)
    CREATE TRIGGER IF NOT EXISTS trg_check_cupo_insert
    BEFORE INSERT ON Reserva
    BEGIN
        SELECT CASE
            WHEN (
                SELECT COUNT(*) FROM Reserva
                WHERE id_clase = NEW.id_clase AND estado_reserva = 'confirmada'
            ) >= (
                SELECT cupo_max FROM Clase WHERE id_clase = NEW.id_clase
            )
            THEN RAISE(ABORT, 'Error: CUPOS_AGOTADOS')
        END;
    END;

    -- Trigger: Validar suscripción activa al reservar
    CREATE TRIGGER IF NOT EXISTS trg_check_vigencia_socio
    BEFORE INSERT ON Reserva
    BEGIN
        SELECT CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM Suscripcion
                WHERE id_socio = NEW.id_socio
                  AND estado_sus = 'activa'
                  AND DATE(fecha_fin) >= DATE('now', 'localtime')
            )
            THEN RAISE(ABORT, 'Error: SIN_SUSCRIPCION_ACTIVA')
        END;
    END;
    """
    with get_conn() as c:
        c.executescript(ddl)
# ============================================================
# SOCIOS (CRUD)
# ============================================================
def get_all_socios() -> List[Dict]:
    try:
        with get_conn() as c:
            # AÑADIDO: WHERE activo = 1
            rows = c.execute("""
                SELECT id_socio, RUT, nombre, apellido_p, apellido_m,
                       telefono, direccion, fecha_nac
                FROM Socio
                WHERE activo = 1
                ORDER BY apellido_p COLLATE NOCASE, nombre COLLATE NOCASE
            """).fetchall()
            return _rows_to_dicts(rows)
    except Exception as e:
        print(f"Error al obtener socios: {e}")
        return []

def buscar_socio_por_rut(rut: str) -> Optional[Dict]:
    try:
        with get_conn() as c:
            row = c.execute("""
                SELECT id_socio, RUT, nombre, apellido_p, apellido_m,
                       telefono, direccion, fecha_nac
                FROM Socio
                WHERE RUT = ?
            """, (rut.strip(),)).fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"Error al buscar socio: {e}")
        return None

def crear_socio(
    rut: str,
    nombre: str,
    apellido_p: str,
    apellido_m: Optional[str],
    fecha_nac: str,        # YYYY-MM-DD
    telefono: Optional[str],
    direccion: Optional[str],
) -> Tuple[bool, Optional[int], Optional[str]]:
    try:
        with get_conn() as c:
            cur = c.execute("""
                INSERT INTO Socio (RUT, nombre, apellido_p, apellido_m,
                                   fecha_nac, telefono, direccion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rut.strip(),
                nombre.strip(),
                apellido_p.strip(),
                (apellido_m or None),
                fecha_nac,
                (telefono or None),
                (direccion or None),
            ))
            return True, cur.lastrowid, None
    except sqlite3.IntegrityError as ie:
        return False, None, str(ie)
    except Exception as e:
        print(f"Error al crear socio: {e}")
        return False, None, str(e)

def actualizar_socio(
    id_socio: int,
    rut: str,
    nombre: str,
    apellido_p: str,
    apellido_m: Optional[str],
    fecha_nac: str,
    telefono: Optional[str],
    direccion: Optional[str],
) -> Tuple[bool, int, Optional[str]]:
    try:
        with get_conn() as c:
            cur = c.execute("""
                UPDATE Socio
                SET RUT = ?, nombre = ?, apellido_p = ?, apellido_m = ?,
                    fecha_nac = ?, telefono = ?, direccion = ?
                WHERE id_socio = ?
            """, (
                rut.strip(),
                nombre.strip(),
                apellido_p.strip(),
                (apellido_m or None),
                fecha_nac,
                (telefono or None),
                (direccion or None),
                id_socio,
            ))
            return True, cur.rowcount, None
    except sqlite3.IntegrityError as ie:
        return False, 0, str(ie)
    except Exception as e:
        print(f"Error al actualizar socio: {e}")
        return False, 0, str(e)

def eliminar_socio(id_socio: int) -> Tuple[bool, int, Optional[str]]:
    try:
        with get_conn() as c:
            # CAMBIO: No borramos, solo desactivamos.
            cur = c.execute("UPDATE Socio SET activo = 0 WHERE id_socio = ?", (id_socio,))
            return True, cur.rowcount, None
    except sqlite3.IntegrityError as ie:
        return False, 0, str(ie)
    except Exception as e:
        print(f"Error al eliminar socio: {e}")
        return False, 0, str(e)

# ============================================================
# DASHBOARD
# ============================================================
def count_socios_activos() -> int:
    with get_conn() as c:
        exists = c.execute("""
            SELECT 1 FROM sqlite_master WHERE type='view' AND name='v_socios_activos'
        """).fetchone()
        if exists:
            row = c.execute("SELECT COUNT(*) AS n FROM v_socios_activos").fetchone()
            return int(row["n"] if row else 0)
        row = c.execute("""
            WITH ult AS (
              SELECT id_socio, MAX(fecha_fin) AS fmax
              FROM Suscripcion GROUP BY id_socio
            )
            SELECT COUNT(*) AS n
            FROM ult u
            JOIN Suscripcion s ON s.id_socio=u.id_socio AND s.fecha_fin=u.fmax
            WHERE s.estado_sus='activa' AND DATE(s.fecha_fin) >= DATE('now','localtime')
        """).fetchone()
        return int(row["n"] if row else 0)

# def proximas_clases(limit: int = 10) -> List[Dict]:
#     with get_conn() as c:
#         rows = c.execute("""
#             SELECT nombre, fecha_hora, cupo_max
#             FROM Clase
#             WHERE datetime(fecha_hora) >= datetime('now','localtime')
#             ORDER BY fecha_hora ASC
#             LIMIT ?
#         """, (limit,)).fetchall()
#         return _rows_to_dicts(rows)

def count_clases_hoy() -> int:
    with get_conn() as c:
        row = c.execute("""
            SELECT COUNT(*) AS n
            FROM Clase
            WHERE DATE(fecha_hora) = DATE('now','localtime')
        """).fetchone()
        return int(row["n"] if row else 0)

def ingresos_mes_actual() -> float:
    with get_conn() as c:
        row = c.execute("""
            SELECT COALESCE(SUM(monto),0) AS total
            FROM Pago
            WHERE estado_pago='completado'
              AND strftime('%Y-%m','now','localtime') = strftime('%Y-%m', fecha_pago)
        """).fetchone()
        return float(row["total"] if row else 0.0)

def membresias_por_vencer(dias: int = 7) -> List[Dict]:
    with get_conn() as c:
        rows = c.execute("""
            SELECT s.id_socio,
                   s.nombre || ' ' || s.apellido_p AS nombre_socio,
                   sus.fecha_fin,
                   p.nombre_plan,
                   CAST(julianday(sus.fecha_fin) - julianday(date('now','localtime')) AS INT) AS dias_restantes
            FROM Suscripcion sus
            JOIN Socio s ON s.id_socio = sus.id_socio
            JOIN Plan  p ON p.id_plan  = sus.id_plan
            WHERE DATE(sus.fecha_fin) BETWEEN DATE('now','localtime')
                                          AND DATE('now','localtime', ?)
            ORDER BY sus.fecha_fin ASC
            LIMIT 50
        """, (f'+{int(dias)} day',)).fetchall()
        return _rows_to_dicts(rows)

# ============================================================
# PAGOS
# ============================================================
def get_historial_pagos(limit: int = 100) -> List[Dict]:
    try:
        with get_conn() as c:
            view_exists = c.execute("""
                SELECT 1 FROM sqlite_master
                WHERE type='view' AND name='v_historial_pagos'
            """).fetchone()
            if view_exists:
                rows = c.execute("""
                    SELECT id_pago, RUT, nombre_socio, nombre_plan,
                           fecha_pago, monto, metodo_pago, estado_pago
                    FROM v_historial_pagos
                    ORDER BY fecha_pago DESC
                    LIMIT ?
                """, (limit,)).fetchall()
            else:
                rows = c.execute("""
                    SELECT pag.id_pago,
                           s.RUT,
                           s.nombre || ' ' || s.apellido_p AS nombre_socio,
                           p.nombre_plan,
                           pag.fecha_pago,
                           pag.monto,
                           pag.metodo_pago,
                           pag.estado_pago
                    FROM Pago pag
                    JOIN Suscripcion sus ON pag.id_suscripcion = sus.id_suscripcion
                    JOIN Socio s ON sus.id_socio = s.id_socio
                    JOIN Plan  p ON sus.id_plan  = p.id_plan
                    ORDER BY pag.fecha_pago DESC
                    LIMIT ?
                """, (limit,)).fetchall()
            return _rows_to_dicts(rows)
    except Exception as e:
        print(f"Error al obtener historial de pagos: {e}")
        return []

def registrar_pago(
    id_suscripcion: int,
    monto: float,
    metodo: str,
    comprobante: Optional[str] = None,
) -> Tuple[bool, Optional[int], Optional[str]]:
    metodo = (metodo or "").strip().lower()
    if metodo not in ("transferencia", "webpay", "tarjeta", "efectivo"):
        return False, None, f"Método no válido: {metodo}"
    try:
        with get_conn() as c:
            cur = c.execute("""
                INSERT INTO Pago (id_suscripcion, monto, metodo_pago, num_comprobante)
                VALUES (?, ?, ?, ?)
            """, (id_suscripcion, monto, metodo, (comprobante or None)))
            return True, cur.lastrowid, None
    except sqlite3.IntegrityError as ie:
        return False, None, str(ie)
    except Exception as e:
        print(f"Error al registrar pago: {e}")
        return False, None, str(e)

# ============================================================
# CLASES / RESERVAS
# ============================================================
def get_all_clases() -> List[Dict]:
    with get_conn() as c:
        rows = c.execute("""
            SELECT
              c.id_clase,
              c.nombre,
              t.nombre AS tipo,
              e.nombre || ' ' || e.apellido AS entrenador,
              c.fecha_hora,
              c.duracion_min,
              c.cupo_max
            FROM Clase c
            JOIN Tipo t ON t.id_tipo = c.id_tipo
            JOIN Entrenador e ON e.id_entrenador = c.id_entrenador
            ORDER BY c.fecha_hora ASC
        """).fetchall()
        return _rows_to_dicts(rows)

def reservar_clase(id_socio: int, id_clase: int) -> Tuple[bool, Optional[int], Optional[str]]:
    try:
        with get_conn() as c:
            cur = c.execute("""
                INSERT INTO Reserva (id_socio, id_clase, estado_reserva, asistio)
                VALUES (?, ?, 'confirmada', 0)
            """, (id_socio, id_clase))
            return True, cur.lastrowid, None
    except sqlite3.IntegrityError as ie:
        return False, None, str(ie)
    except Exception as e:
        print(f"Error al reservar clase: {e}")
        return False, None, str(e)

# =========================
# PLANES
# =========================
def get_planes():
    """Devuelve lista de planes disponibles (id, nombre, meses, precio)."""
    with get_conn() as c:
        rows = c.execute("""
            SELECT id_plan, nombre_plan, duracion_meses, precio
            FROM Plan
            ORDER BY precio DESC
        """).fetchall()
        return [dict(r) for r in rows] if rows is not None else None

def ensure_seed_planes():
    """Semilla mínima de planes (ejecuta una sola vez si tu tabla Plan está vacía)."""
    with get_conn() as c:
        n = c.execute("SELECT COUNT(*) AS n FROM Plan").fetchone()["n"]
        if n and n > 0:
            return 0
        c.executemany("""
            INSERT INTO Plan (nombre_plan, precio, duracion_meses, limite_clases, beneficio, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ('Plan Mensual',   24500, 1, 20, 'Matrícula gratis|Evaluación InBody', 'Mensual estándar'),
            ('Plan Trimestral', 66000, 3, 20, 'Evaluación y programa',              'Tramo 3 meses'),
            ('Plan Semestral', 120000,6, None,'2 sesiones PT',                      '6 meses'),
            ('Plan Anual',     210000,12,None,'PT|Eval completa|2 meses regalo',    '12 meses'),
        ])
        return 4

# =========================
# SUSCRIPCIONES
# =========================
def crear_suscripcion(id_socio: int, id_plan: int, fecha_inicio: str, estado: str = "activa"):
    """
    Crea una suscripción para un socio calculando fecha_fin a partir del plan.
    fecha_inicio en 'YYYY-MM-DD'. Devuelve (ok, id_suscripcion, error_msg).
    """
    with get_conn() as c:
        # calcula fecha_fin sumando meses del plan directamente en SQLite
        row = c.execute("""
            SELECT DATE(?, printf('+%d months', duracion_meses)) AS fecha_fin
            FROM Plan WHERE id_plan = ?
        """, (fecha_inicio, id_plan)).fetchone()
        if not row:
            return False, None, "Plan no encontrado"
        fecha_fin = row["fecha_fin"]
        try:
            cur = c.execute("""
                INSERT INTO Suscripcion (id_socio, id_plan, fecha_inicio, fecha_fin, estado_sus)
                VALUES (?, ?, ?, ?, ?)
            """, (id_socio, id_plan, fecha_inicio, fecha_fin, estado))
            return True, cur.lastrowid, None
        except sqlite3.IntegrityError as ie:
            return False, None, str(ie)
        except Exception as e:
            return False, None, str(e)

def get_suscripciones_por_socio(id_socio: int):
    """Lista todas las suscripciones de un socio (la más reciente primero)."""
    with get_conn() as c:
        rows = c.execute("""
            SELECT sus.id_suscripcion, sus.fecha_inicio, sus.fecha_fin, sus.estado_sus,
                   p.id_plan, p.nombre_plan, p.duracion_meses, p.precio
            FROM Suscripcion sus
            JOIN Plan p ON p.id_plan = sus.id_plan
            WHERE sus.id_socio = ?
            ORDER BY sus.fecha_fin DESC
        """, (id_socio,)).fetchall()
        return [dict(r) for r in rows] if rows is not None else None

def get_suscripcion_activa_por_socio(id_socio: int):
    """
    Devuelve la suscripción activa más reciente si existe (o None).
    Activa = estado_sus='activa' y fecha_fin >= hoy.
    """
    with get_conn() as c:
        row = c.execute("""
            WITH ult AS(
              SELECT id_socio, MAX(fecha_fin) AS fmax
              FROM Suscripcion WHERE id_socio=? GROUP BY id_socio
            )
            SELECT sus.*, p.precio, p.nombre_plan
            FROM ult u
            JOIN Suscripcion sus ON sus.id_socio=u.id_socio AND sus.fecha_fin=u.fmax
            JOIN Plan p ON p.id_plan = sus.id_plan
            WHERE sus.estado_sus='activa' AND DATE(sus.fecha_fin) >= DATE('now','localtime')
        """, (id_socio,)).fetchone()
        return dict(row) if row else None

def actualizar_estados_suscripciones():

    with get_conn() as c:
        c.execute("""
            UPDATE Suscripcion
            SET estado_sus = CASE
                WHEN DATE(fecha_fin) >= DATE('now','localtime') THEN 'activa'
                ELSE 'vencida'
            END
        """)

# =========================
# CLASSE
# =========================

def get_all_classes() -> List[Dict] | None:

    with get_conn() as c:
        rows = c.execute("""
            SELECT
              c.id_clase,
              c.nombre,
              t.nombre AS tipo_clase,
              e.nombre || ' ' || e.apellido AS entrenador,
              c.fecha_hora,
              c.duracion_min,
              c.descripcion,
              c.cupo_max,
              (c.cupo_max - COALESCE(SUM(CASE WHEN r.estado_reserva='confirmada' THEN 1 ELSE 0 END),0)) AS cupos_disponibles
            FROM Clase c
            JOIN Tipo t ON t.id_tipo = c.id_tipo
            JOIN Entrenador e ON e.id_entrenador = c.id_entrenador
            LEFT JOIN Reserva r ON r.id_clase = c.id_clase
            GROUP BY c.id_clase
            ORDER BY c.fecha_hora ASC
        """).fetchall()
        return [dict(r) for r in rows] if rows is not None else None

def get_all_proximas_clases(limit: int | None = None) -> List[Dict] | None:

    with get_conn() as c:
        query = """
            SELECT
              c.id_clase,
              c.nombre,
              t.nombre AS tipo_clase,
              e.nombre || ' ' || e.apellido AS entrenador,
              c.fecha_hora,
              c.duracion_min,
              c.descripcion,
              c.cupo_max,
              (c.cupo_max - COALESCE(SUM(CASE WHEN r.estado_reserva='confirmada' THEN 1 ELSE 0 END),0)) AS cupos_disponibles
            FROM Clase c
            JOIN Tipo t ON t.id_tipo = c.id_tipo
            JOIN Entrenador e ON e.id_entrenador = c.id_entrenador
            LEFT JOIN Reserva r ON r.id_clase = c.id_clase
            WHERE datetime(c.fecha_hora) >= datetime('now','localtime')
            GROUP BY c.id_clase
            ORDER BY c.fecha_hora ASC
        """
        
        if limit:
            query += " LIMIT ?"
            rows = c.execute(query, (limit,)).fetchall()
        else:
            rows = c.execute(query).fetchall()
            
        return [dict(r) for r in rows] if rows is not None else None


def get_clases_disponibles() -> List[Dict] | None:

    with get_conn() as c:
        rows = c.execute("""
            SELECT
              c.id_clase,
              c.nombre,
              t.nombre AS tipo_clase,
              e.nombre || ' ' || e.apellido AS entrenador,
              c.fecha_hora,
              c.duracion_min,
              c.descripcion,
              c.cupo_max,
              (c.cupo_max - COALESCE(SUM(CASE WHEN r.estado_reserva='confirmada' THEN 1 ELSE 0 END),0)) AS cupos_disponibles
            FROM Clase c
            JOIN Tipo t ON t.id_tipo = c.id_tipo
            JOIN Entrenador e ON e.id_entrenador = c.id_entrenador
            LEFT JOIN Reserva r ON r.id_clase = c.id_clase
            WHERE datetime(c.fecha_hora) >= datetime('now','localtime')
            GROUP BY c.id_clase
            HAVING cupos_disponibles > 0
            ORDER BY c.fecha_hora ASC
        """).fetchall()
        return [dict(r) for r in rows] if rows is not None else None

def get_all_clases_pasadas() -> List[Dict] | None:

    with get_conn() as c:
        rows = c.execute("""
            SELECT
              c.id_clase,
              c.nombre,
              t.nombre AS tipo_clase,
              e.nombre || ' ' || e.apellido AS entrenador,
              c.fecha_hora,
              c.duracion_min,
              c.descripcion,
              c.cupo_max,
              (c.cupo_max - COALESCE(SUM(CASE WHEN r.estado_reserva='confirmada' THEN 1 ELSE 0 END),0)) AS cupos_disponibles
            FROM Clase c
            JOIN Tipo t ON t.id_tipo = c.id_tipo
            JOIN Entrenador e ON e.id_entrenador = c.id_entrenador
            LEFT JOIN Reserva r ON r.id_clase = c.id_clase
            WHERE datetime(c.fecha_hora) < datetime('now','localtime')
            GROUP BY c.id_clase
            ORDER BY c.fecha_hora DESC
        """).fetchall()
        return [dict(r) for r in rows] if rows is not None else None

def registrar_nueva_classe(
    id_entrenador: int,
    id_tipo: int,
    nombre: str,
    descripcion: Optional[str],
    fecha_hora: str,
    duracion_min: int,
    cupo_max: int
) -> Tuple[bool, Optional[int], Optional[str]]:

    try:
        with get_conn() as c:
            cur = c.execute("""
                INSERT INTO Clase (id_entrenador, id_tipo, nombre, descripcion,
                                   fecha_hora, duracion_min, cupo_max)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                id_entrenador,
                id_tipo,
                nombre.strip(),
                (descripcion or None),
                fecha_hora,
                duracion_min,
                cupo_max
            ))
            return True, cur.lastrowid, None
    except sqlite3.IntegrityError as ie:
        return False, None, str(ie)
    except Exception as e:
        print(f"Error al registrar clase: {e}")
        return False, None, str(e)

# =========================
# ENTRENADORES
# =========================

def get_all_entrenadores() -> List[Dict] | None:
    """Devuelve todos los entrenadores registrados."""
    with get_conn() as c:
        rows = c.execute("""
            SELECT
              id_entrenador,
              RUT,
              nombre,
              apellido,
              telefono,
              fecha_nac,
              especialidad
            FROM Entrenador
            ORDER BY apellido COLLATE NOCASE, nombre COLLATE NOCASE
        """).fetchall()
        return [dict(r) for r in rows] if rows is not None else None

# =========================
# Tipo
# =========================

def get_all_tipos() -> List[Dict] | None:
    """Devuelve todos los tipos de clases registrados."""
    with get_conn() as c:
        rows = c.execute("""
            SELECT
              id_tipo,
              nombre,
              descripcion
            FROM Tipo
            ORDER BY nombre COLLATE NOCASE
        """).fetchall()
        return [dict(r) for r in rows] if rows is not None else None

# ============================================================
# DASHBOARD
# ============================================================

def count_entrenadores_activos() -> int:
    with get_conn() as c:
        row = c.execute("SELECT COUNT(*) AS n FROM Entrenador").fetchone()
        return int(row["n"] if row else 0)

def count_reservas_hoy() -> int:
    with get_conn() as c:
        row = c.execute("""
            SELECT COUNT(*) AS n 
            FROM Reserva r
            JOIN Clase c ON r.id_clase = c.id_clase
            WHERE DATE(c.fecha_hora) = DATE('now','localtime') 
            AND r.estado_reserva = 'confirmada'
        """).fetchone()
        return int(row["n"] if row else 0)

def get_clases_proximas_con_alertas() -> List[Dict]:
    with get_conn() as c:
        rows = c.execute("""
            SELECT
                c.id_clase,
                c.nombre,
                c.cupo_max,
                (c.cupo_max - COUNT(r.id_reserva)) as cupos_disponibles
            FROM Clase c
            LEFT JOIN Reserva r ON c.id_clase = r.id_clase AND r.estado_reserva = 'confirmada'
            WHERE datetime(c.fecha_hora) >= datetime('now','localtime')
            GROUP BY c.id_clase
            HAVING cupos_disponibles <= 3
            ORDER BY c.fecha_hora
        """).fetchall()
        return [dict(r) for r in rows] if rows else []

def get_clases_by_type_stats() -> List[Dict]:
    """Récupère les statistiques des cours par type"""
    with get_conn() as c:
        rows = c.execute("""
            SELECT 
                t.nombre as tipo,
                COUNT(c.id_clase) as cantidad,
                AVG(c.duracion_min) as duracion_promedio,
                SUM(c.cupo_max) as cupos_totales
            FROM Clase c
            JOIN Tipo t ON c.id_tipo = t.id_tipo
            GROUP BY t.nombre
            ORDER BY cantidad DESC
        """).fetchall()
        return [dict(r) for r in rows] if rows else []

def get_payment_methods_stats() -> List[Dict]:
    """Récupère les statistiques des méthodes de paiement"""
    with get_conn() as c:
        rows = c.execute("""
            SELECT 
                metodo_pago,
                COUNT(*) as cantidad,
                SUM(monto) as total,
                AVG(monto) as promedio
            FROM Pago
            WHERE estado_pago = 'completado'
            GROUP BY metodo_pago
            ORDER BY total DESC
        """).fetchall()
        return [dict(r) for r in rows] if rows else []


def get_stats_last_7_days() -> Dict[str, List]:

    from datetime import datetime, timedelta

    fechas = []
    mapa_res = {}
    mapa_cla = {}

    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        fechas.append(d)
        mapa_res[d] = 0
        mapa_cla[d] = 0

    with get_conn() as c:

        rows_res = c.execute("""
            SELECT DATE(fecha_reserva) as dia, COUNT(*) as n
            FROM Reserva
            WHERE DATE(fecha_reserva) >= DATE('now', '-6 days')
            GROUP BY DATE(fecha_reserva)
        """).fetchall()

        for r in rows_res:
            if r['dia'] in mapa_res:
                mapa_res[r['dia']] = r['n']


        rows_cla = c.execute("""
            SELECT DATE(fecha_hora) as dia, COUNT(*) as n
            FROM Clase
            WHERE DATE(fecha_hora) >= DATE('now', '-6 days')
            GROUP BY DATE(fecha_hora)
        """).fetchall()

        for r in rows_cla:
            if r['dia'] in mapa_cla:
                mapa_cla[r['dia']] = r['n']

    # Formatear para el gráfico (DD/MM)
    fechas_fmt = [f[8:] + "/" + f[5:7] for f in fechas]

    return {
        "fechas": fechas_fmt,
        "reservas": [mapa_res[f] for f in fechas],
        "clases": [mapa_cla[f] for f in fechas]
    }


def init_db_data():

    with get_conn() as c:
        # 1. Verificar si ya existen datos
        if c.execute("SELECT COUNT(*) as n FROM Plan").fetchone()['n'] > 0:
            return

        print("📥 Inyectando datos maestros inteligentes...")
        from datetime import datetime, timedelta

        # Helpers de fecha
        hoy = datetime.now()
        ayer = (hoy - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        manana = (hoy + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        pasado_ma = (hoy + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

        inicio_sub = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')  # Empezó hace un mes
        fin_sub_ok = (hoy + timedelta(days=330)).strftime('%Y-%m-%d')  # Termina en un año
        fin_sub_bad = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')  # Venció ayer

        try:

            c.executemany("""
                INSERT INTO Plan (nombre_plan, precio, duracion_meses, limite_clases, beneficio, descripcion) VALUES (?,?,?,?,?,?)
            """, [
                ('Plan Anual', 17500, 12, None,
                 'Matrícula gratis|Personal trainer|Evaluación completa|2 meses de regalo',
                 'Plan anual con descuento especial'),
                ('Plan Mensual', 24500, 1, 20, 'Matrícula gratis|Personal trainer|Evaluación InBody',
                 'Plan mensual con cargo automático'),
                ('Plan Trimestral', 22000, 3, 20, 'Matrícula gratis|Evaluación y programa', 'Plan por 3 meses'),
                ('Plan Semestral', 20000, 6, None, 'Matrícula gratis|2 sesiones personal trainer', 'Plan de 6 meses')
            ])


            c.executemany("""
                INSERT INTO Socio (RUT, nombre, apellido_p, apellido_m, fecha_nac, telefono, direccion, activo) VALUES (?,?,?,?,?,?,?,1)
            """, [
                ('12345678-9', 'Pedro', 'Sánchez', 'García', '1990-05-15', '912345678', 'Av. Providencia 123'),
                ('98765432-1', 'María', 'López', 'Fernández', '1985-08-22', '987654321', 'Calle Los Alerces 456'),
                ('11223344-5', 'Carlos', 'Rodríguez', 'Martínez', '1992-11-30', '923456789', 'Pasaje Las Rosas 789'),
                ('55667788-9', 'Ana', 'González', 'Torres', '1988-03-12', '945678901', 'Av. Libertador 321'),
                ('99887766-5', 'Luis', 'Morales', 'Silva', '1995-07-25', '956789012', 'Calle Nueva 654')
            ])


            c.executemany("""
                INSERT INTO Suscripcion (id_socio, id_plan, fecha_inicio, fecha_fin, estado_sus) VALUES (?,?,?,?,?)
            """, [
                (1, 1, inicio_sub, fin_sub_ok, 'activa'),
                (2, 2, inicio_sub, fin_sub_ok, 'activa'),
                (3, 3, inicio_sub, fin_sub_ok, 'activa'),
                (4, 4, inicio_sub, fin_sub_ok, 'activa'),
                (5, 2, inicio_sub, fin_sub_bad, 'vencida')  # Luis está vencido
            ])


            c.executemany("""
                INSERT INTO Pago (id_suscripcion, fecha_pago, monto, metodo_pago, estado_pago, num_comprobante) VALUES (?,?,?,?,?,?)
            """, [
                (1, inicio_sub, 210000, 'transferencia', 'completado', 'COMP-001'),
                (2, inicio_sub, 24500, 'webpay', 'completado', 'COMP-002'),
                (3, inicio_sub, 66000, 'efectivo', 'completado', 'COMP-003'),
                (4, inicio_sub, 120000, 'transferencia', 'completado', 'COMP-004'),
                (5, inicio_sub, 24500, 'tarjeta', 'completado', 'COMP-005')
            ])


            c.executemany("INSERT INTO Tipo (nombre, descripcion) VALUES (?,?)", [
                ('Funcional', 'Entrenamiento funcional con peso corporal'),
                ('Spinning', 'Ciclismo indoor de alta intensidad'),
                ('HIIT', 'High Intensity Interval Training')
            ])

            c.executemany(
                "INSERT INTO Entrenador (RUT, nombre, apellido, telefono, fecha_nac, especialidad) VALUES (?,?,?,?,?,?)",
                [
                    ('20111222-3', 'Juan', 'Pérez', '933445566', '1985-03-15', 'Spinning'),
                    ('20222333-4', 'María', 'González', '944556677', '1990-07-22', 'Funcional'),
                    ('20333444-5', 'Carlos', 'Ruiz', '955667788', '1988-11-30', 'CrossFit')
                ])


            c.executemany("""
                INSERT INTO Clase (id_entrenador, id_tipo, nombre, descripcion, fecha_hora, duracion_min, cupo_max) VALUES (?,?,?,?,?,?,?)
            """, [
                # Clase 1: AYER (Para historial)
                (1, 2, 'Spinning Matutino', 'Clase nivel intermedio', ayer, 45, 25),
                # Clase 2: MAÑANA (Para reservar)
                (3, 1, 'Funcional Tarde', 'Entrenamiento funcional', manana, 60, 20),
                # Clase 3: PASADO MAÑANA
                (3, 3, 'HIIT Extremo', 'Alta intensidad', pasado_ma, 45, 15),
                # Clase 4: MAÑANA Noche
                (1, 2, 'Spinning Noche', 'Clase avanzada', manana, 50, 25)
            ])


            c.executemany("""
                INSERT INTO Reserva (id_socio, id_clase, estado_reserva, asistio) VALUES (?,?,?,?)
            """, [
                (1, 1, 'confirmada', 1),  # Pedro fue ayer (asistió)
                (2, 1, 'confirmada', 1),  # Maria fue ayer
                (3, 2, 'confirmada', 0),  # Carlos va mañana
                (4, 3, 'confirmada', 0),  # Ana va pasado mañana
                (1, 4, 'confirmada', 0)  # Pedro repite mañana
            ])

            print("✅ Datos cargados exitosamente.")
        except Exception as e:
            print(f"❌ Error cargando datos seed: {e}")