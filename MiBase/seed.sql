
PRAGMA foreign_keys = ON;

INSERT INTO Plan (nombre_plan, precio, duracion_meses, limite_clases, beneficio, descripcion) VALUES
('Plan Anual', 17500, 12, NULL, 'Matrícula gratis|Personal trainer|Evaluación completa|2 meses de regalo', 'Plan anual con descuento especial'),
('Plan Mensual', 24500, 1, 20, 'Matrícula gratis|Personal trainer|Evaluación InBody', 'Plan mensual con cargo automático'),
('Plan Trimestral', 22000, 3, 20, 'Matrícula gratis|Evaluación y programa', 'Plan por 3 meses'),
('Plan Semestral', 20000, 6, NULL, 'Matrícula gratis|2 sesiones personal trainer', 'Plan de 6 meses');

INSERT INTO Socio (RUT, nombre, apellido_p, apellido_m, fecha_nac, telefono, direccion) VALUES
('12345678-9', 'Pedro', 'Sánchez', 'García', '1990-05-15', '912345678', 'Av. Providencia 123'),
('98765432-1', 'María', 'López', 'Fernández', '1985-08-22', '987654321', 'Calle Los Alerces 456'),
('11223344-5', 'Carlos', 'Rodríguez', 'Martínez', '1992-11-30', '923456789', 'Pasaje Las Rosas 789'),
('55667788-9', 'Ana', 'González', 'Torres', '1988-03-12', '945678901', 'Av. Libertador 321'),
('99887766-5', 'Luis', 'Morales', 'Silva', '1995-07-25', '956789012', 'Calle Nueva 654');

INSERT INTO Suscripcion (id_socio, id_plan, fecha_inicio, fecha_fin, estado_sus) VALUES
(1, 1, '2024-10-01', '2025-10-01', 'activa'),
(2, 2, '2025-10-01', '2025-11-01', 'activa'),
(3, 3, '2025-09-01', '2025-12-01', 'activa'),
(4, 4, '2025-08-01', '2026-02-01', 'activa'),
(5, 2, '2025-09-15', '2025-10-15', 'vencida');

INSERT INTO Pago (id_suscripcion, fecha_pago, monto, metodo_pago, estado_pago, num_comprobante) VALUES
(1, '2024-10-01', 210000, 'transferencia', 'completado', 'COMP-2024-001'),
(2, '2025-10-01', 24500, 'webpay', 'completado', 'COMP-2025-002'),
(3, '2025-09-01', 66000, 'efectivo', 'completado', 'COMP-2025-003'),
(4, '2025-08-01', 120000, 'transferencia', 'completado', 'COMP-2025-004'),
(5, '2025-09-15', 24500, 'tarjeta', 'completado', 'COMP-2025-005');

INSERT INTO Tipo (nombre, descripcion) VALUES
('Funcional', 'Entrenamiento funcional con peso corporal'),
('Spinning', 'Ciclismo indoor de alta intensidad'),
('HIIT', 'High Intensity Interval Training');

INSERT INTO Entrenador (RUT, nombre, apellido, telefono, fecha_nac, especialidad) VALUES
('20111222-3', 'Juan', 'Pérez', '933445566', '1985-03-15', 'Spinning'),
('20222333-4', 'María', 'González', '944556677', '1990-07-22', 'Funcional'),
('20333444-5', 'Carlos', 'Ruiz', '955667788', '1988-11-30', 'CrossFit');

INSERT INTO Clase (id_entrenador, id_tipo, nombre, descripcion, fecha_hora, duracion_min, cupo_max) VALUES
(1, 2, 'Spinning Matutino', 'Clase de spinning nivel intermedio', '2025-10-15 08:00:00', 45, 25),
(3, 1, 'Funcional Tarde', 'Entrenamiento funcional para todos', '2025-10-15 18:00:00', 60, 20),
(3, 3, 'HIIT Extremo', 'Entrenamiento de alta intensidad', '2025-10-16 19:00:00', 45, 15),
(1, 2, 'Spinning Noche', 'Clase de spinning avanzada', '2025-10-16 20:00:00', 50, 25);

INSERT INTO Reserva (id_socio, id_clase, estado_reserva, asistio) VALUES
(1, 1, 'confirmada', 0),
(2, 1, 'confirmada', 0),
(3, 2, 'confirmada', 0),
(4, 3, 'pendiente', 0),
(1, 4, 'confirmada', 0);

UPDATE Suscripcion
SET estado_sus = CASE
  WHEN DATE(fecha_fin) >= DATE('now','localtime') THEN 'activa'
  ELSE 'vencida'
END;
