
PRAGMA foreign_keys = OFF;
BEGIN;

DROP VIEW IF EXISTS v_socios_inactivo;
DROP VIEW IF EXISTS v_socios_activos;
DROP VIEW IF EXISTS v_historial_pagos;

DROP TRIGGER IF EXISTS trg_entrenador_fecha_ins;
DROP TRIGGER IF EXISTS trg_entrenador_fecha_upd;

DROP TABLE IF EXISTS Reserva;
DROP TABLE IF EXISTS Clase;
DROP TABLE IF EXISTS Entrenador;
DROP TABLE IF EXISTS Tipo;
DROP TABLE IF EXISTS Pago;
DROP TABLE IF EXISTS Suscripcion;
DROP TABLE IF EXISTS Plan;
DROP TABLE IF EXISTS Socio;

COMMIT;
PRAGMA foreign_keys = ON;
