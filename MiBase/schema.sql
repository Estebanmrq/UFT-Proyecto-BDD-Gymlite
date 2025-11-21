
PRAGMA foreign_keys = ON;

CREATE TABLE Socio (
    id_socio INTEGER PRIMARY KEY AUTOINCREMENT,
    RUT VARCHAR(12) NOT NULL UNIQUE,
    nombre VARCHAR(50) NOT NULL,
    apellido_p VARCHAR(50) NOT NULL,
    apellido_m VARCHAR(50),
    fecha_nac DATE NOT NULL,
    telefono VARCHAR(12),
    direccion VARCHAR(100),
    CHECK (LENGTH(RUT) >= 9)
);

CREATE TABLE Plan (
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

CREATE TABLE Suscripcion (
    id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_socio INTEGER NOT NULL,
    id_plan INTEGER NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado_sus VARCHAR(20) NOT NULL DEFAULT 'activa',
    FOREIGN KEY (id_socio) REFERENCES Socio(id_socio) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_plan) REFERENCES Plan(id_plan) ON DELETE RESTRICT ON UPDATE CASCADE,
    CHECK (estado_sus IN ('activa', 'vencida', 'cancelada')),
    CHECK (fecha_fin > fecha_inicio)
);

CREATE INDEX idx_suscripcion_socio ON Suscripcion(id_socio);
CREATE INDEX idx_suscripcion_plan ON Suscripcion(id_plan);

CREATE TABLE Pago (
    id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    id_suscripcion INTEGER NOT NULL,
    fecha_pago DATE NOT NULL DEFAULT (DATE('now')),
    monto DECIMAL(10,2) NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL,
    estado_pago VARCHAR(20) NOT NULL DEFAULT 'completado',
    num_comprobante VARCHAR(50),
    FOREIGN KEY (id_suscripcion) REFERENCES Suscripcion(id_suscripcion) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (monto > 0),
    CHECK (metodo_pago IN ('transferencia', 'webpay', 'tarjeta', 'efectivo')),
    CHECK (estado_pago IN ('pendiente', 'completado', 'rechazado'))
);

CREATE INDEX idx_pago_suscripcion ON Pago(id_suscripcion);

CREATE TABLE Tipo (
    id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE Entrenador (
    id_entrenador INTEGER PRIMARY KEY AUTOINCREMENT,
    RUT VARCHAR(12) NOT NULL UNIQUE,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    telefono VARCHAR(12),
    fecha_nac DATE NOT NULL,
    especialidad VARCHAR(80) NOT NULL,
    CHECK (LENGTH(RUT) >= 9)
);

CREATE INDEX idx_entrenador_rut ON Entrenador(RUT);

CREATE TABLE Clase (
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

CREATE INDEX idx_clase_entrenador ON Clase(id_entrenador);
CREATE INDEX idx_clase_tipo ON Clase(id_tipo);
CREATE INDEX idx_clase_fecha ON Clase(fecha_hora);

CREATE TABLE Reserva (
    id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    id_socio INTEGER NOT NULL,
    id_clase INTEGER NOT NULL,
    fecha_reserva DATETIME NOT NULL DEFAULT (DATETIME('now')),
    estado_reserva VARCHAR(20) NOT NULL DEFAULT 'confirmada',
    asistio INTEGER DEFAULT 0,
    FOREIGN KEY (id_socio) REFERENCES Socio(id_socio) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_clase) REFERENCES Clase(id_clase) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (estado_reserva IN ('pendiente', 'confirmada', 'cancelada')),
    CHECK (asistio IN (0, 1)),
    UNIQUE (id_socio, id_clase)
);

CREATE INDEX idx_reserva_socio ON Reserva(id_socio);
CREATE INDEX idx_reserva_clase ON Reserva(id_clase);

CREATE TRIGGER trg_entrenador_fecha_ins
BEFORE INSERT ON Entrenador
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN DATE(NEW.fecha_nac) >= DATE('now','localtime') THEN
            RAISE(ABORT, 'fecha_nac no puede ser hoy ni futura')
    END;
END;

CREATE TRIGGER trg_entrenador_fecha_upd
BEFORE UPDATE OF fecha_nac ON Entrenador
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN DATE(NEW.fecha_nac) >= DATE('now','localtime') THEN
            RAISE(ABORT, 'fecha_nac no puede ser hoy ni futura')
    END;
END;

CREATE VIEW v_socios_activos AS
WITH ult AS (
  SELECT id_socio, MAX(fecha_fin) AS fecha_fin_max
  FROM Suscripcion
  GROUP BY id_socio
)
SELECT 
    s.id_socio,
    s.RUT,
    s.nombre || ' ' || s.apellido_p AS nombre_completo,
    s.telefono,
    p.nombre_plan,
    sus.fecha_inicio,
    sus.fecha_fin,
    'Vigente' AS vigencia
FROM ult
JOIN Suscripcion sus
  ON sus.id_socio = ult.id_socio AND sus.fecha_fin = ult.fecha_fin_max
JOIN Socio s ON s.id_socio = sus.id_socio
JOIN Plan  p ON p.id_plan = sus.id_plan
WHERE sus.estado_sus = 'activa'
  AND DATE(sus.fecha_fin) >= DATE('now','localtime');

CREATE VIEW v_socios_inactivo AS
WITH ult AS (
  SELECT id_socio, MAX(fecha_fin) AS fecha_fin_max
  FROM Suscripcion
  GROUP BY id_socio
)
SELECT 
    s.id_socio,
    s.RUT,
    s.nombre || ' ' || s.apellido_p AS nombre_completo,
    s.telefono,
    p.nombre_plan,
    sus.fecha_inicio,
    sus.fecha_fin,
    'Inactiva' AS inactiva
FROM ult
JOIN Suscripcion sus
  ON sus.id_socio = ult.id_socio AND sus.fecha_fin = ult.fecha_fin_max
JOIN Socio s ON s.id_socio = sus.id_socio
JOIN Plan  p ON p.id_plan = sus.id_plan
WHERE sus.estado_sus = 'vencida'
   OR DATE(sus.fecha_fin) < DATE('now','localtime');

CREATE VIEW v_historial_pagos AS
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
INNER JOIN Suscripcion sus ON pag.id_suscripcion = sus.id_suscripcion
INNER JOIN Socio s ON sus.id_socio = s.id_socio
INNER JOIN Plan p ON sus.id_plan = p.id_plan
ORDER BY pag.fecha_pago DESC;
