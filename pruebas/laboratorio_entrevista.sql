-- =========================================================================
-- LABORATORIO PARA LA ENTREVISTA TÉCNICA (Grupo 8, Fase 2)
--
-- Cómo usarlo en MySQL Workbench (localhost, puerto 3307, root / Parques2026):
--   * Poner el cursor en una sentencia y apretar Ctrl + Enter (ejecuta solo esa).
--   * No ejecutar todo el archivo con el rayo grande: muchas sentencias dan
--     error a propósito y Workbench se detiene en el primero.
--
-- No deja cambios: lo que modifica datos va entre START TRANSACTION y ROLLBACK,
-- y lo que quita una restricción la vuelve a poner al final.
-- Si algo queda raro (en la carpeta pmv_parques): docker compose down -v  y  docker compose up -d
-- =========================================================================
USE Sistema_Integral_Parques_Naturales;


-- =========================================================================
-- PARTE 1. DATOS MALOS: cada restricción frena uno (todas deben dar error)
-- =========================================================================

-- 1062 UNIQUE: el visitante V-0074 ya está inscrito en EX-001
INSERT INTO Inscripcion (Registro_Codigo, Id_Visitante, Fecha_Inscripcion, Asistencia)
VALUES ('EX-001', 'V-0074', '2026-01-01', 'Asiste');

-- 3819 CHECK: la nota va de 1 a 7
INSERT INTO Evaluacion (Registro_Codigo, Numero_Evaluacion, Id_Visitante, Fecha_Evaluacion, Calificacion)
VALUES ('EX-001', 99, 'V-0141', '2026-02-01', 8);

-- 3819 CHECK: la asistencia solo puede ser Pendiente, Asiste o No Asiste
UPDATE Inscripcion SET Asistencia = 'Quizas'
WHERE Registro_Codigo = 'EX-001' AND Id_Visitante = 'V-0074';

-- 3819 CHECK: la capacidad va de 1 a 500
UPDATE Excursiones SET Capacidad = 0 WHERE Registro_Codigo = 'EX-001';

-- 3819 CHECK: el tipo solo puede ser Vegetal, Animal o Mineral (NULL sí se acepta)
UPDATE Especie SET Tipo_Especie = 'Hongo' WHERE Id_Especie = 1;

-- 3819 CHECK: un mineral necesita roca o cristales
INSERT INTO Especie_Mineral (Id_Especie, Roca, Cristales) VALUES (1, NULL, NULL);

-- 3819 CHECK: nadie se supervisa a sí mismo
UPDATE Trabajadores SET Run_Supervisor = Run WHERE Run = '11756636-6';

-- 3819 CHECK: el año del parque debe ser el de su fecha de declaración
UPDATE Parque_Natural SET Anio_de_Declaracion = 1975
WHERE Anio_de_Declaracion = 1974 AND Numero_Correlativo = 1;

-- 1048 NOT NULL: el visitante necesita nombre
INSERT INTO Visitantes (Id_Visitante, Nombre_Visitante, Correo_Electronico)
VALUES ('V-9999', NULL, 'prueba@correo.cl');

-- 1062 PRIMARY KEY: el Id V-0141 ya existe
INSERT INTO Visitantes (Id_Visitante, Nombre_Visitante, Correo_Electronico)
VALUES ('V-0141', 'Prueba', 'nuevo@correo.cl');

-- 1452 FK: la excursión EX-999 no existe
INSERT INTO Inscripcion (Registro_Codigo, Id_Visitante, Fecha_Inscripcion)
VALUES ('EX-999', 'V-0074', '2026-01-01');

-- 1452 FK compuesta: no existe el parque (2030, 9)
INSERT INTO Area (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno, Nombre_de_Area,
                  Extension, Nivel_Acceso, Estado_Operativo)
VALUES (2030, 9, 1, 'Area fantasma', 10, 'Libre', 'Operativa');

-- 1451 FK: no se puede borrar un parque que tiene áreas
DELETE FROM Parque_Natural WHERE Anio_de_Declaracion = 1974 AND Numero_Correlativo = 1;

-- 1451 FK: no se puede borrar una especie que tiene subtipo e inventario
DELETE FROM Especie WHERE Id_Especie = 1;

-- Esto SÍ funciona: una especie sin clasificar (Tipo_Especie en NULL)
START TRANSACTION;
UPDATE Especie SET Tipo_Especie = NULL WHERE Id_Especie = 1;
SELECT Id_Especie, Nombre_Vulgar, Tipo_Especie FROM Especie WHERE Id_Especie = 1;
ROLLBACK;


-- =========================================================================
-- PARTE 2. ¿QUÉ PASA SI SE QUITA LA RESTRICCIÓN?
-- =========================================================================

-- 2.1 Sin el CHECK de la nota, entra un 8
ALTER TABLE Evaluacion DROP CHECK Evaluacion_chk_2;
START TRANSACTION;
INSERT INTO Evaluacion (Registro_Codigo, Numero_Evaluacion, Id_Visitante, Fecha_Evaluacion, Calificacion)
VALUES ('EX-001', 99, 'V-0141', '2026-02-01', 8);
SELECT Registro_Codigo, Numero_Evaluacion, Calificacion FROM Evaluacion WHERE Numero_Evaluacion = 99;
ROLLBACK;
-- volver a ponerlo
ALTER TABLE Evaluacion ADD CONSTRAINT Evaluacion_chk_2 CHECK (Calificacion BETWEEN 1 AND 7);

-- 2.2 Sin el UNIQUE de Inscripcion, la misma persona queda inscrita dos veces
-- Directo da error 1553: la FK hacia Excursiones también usa ese índice
ALTER TABLE Inscripcion DROP INDEX Registro_Codigo;
-- Por eso primero se crea un índice normal y después se borra el UNIQUE
ALTER TABLE Inscripcion ADD INDEX idx_registro (Registro_Codigo);
ALTER TABLE Inscripcion DROP INDEX Registro_Codigo;
START TRANSACTION;
INSERT INTO Inscripcion (Registro_Codigo, Id_Visitante, Fecha_Inscripcion, Asistencia)
VALUES ('EX-001', 'V-0074', '2026-01-01', 'Asiste');
SELECT Id_Inscripcion, Registro_Codigo, Id_Visitante, Asistencia
FROM Inscripcion WHERE Registro_Codigo = 'EX-001' AND Id_Visitante = 'V-0074';
ROLLBACK;
-- volver a ponerlo (y el INSERT de arriba vuelve a dar 1062)
ALTER TABLE Inscripcion ADD CONSTRAINT Registro_Codigo UNIQUE (Registro_Codigo, Id_Visitante);
ALTER TABLE Inscripcion DROP INDEX idx_registro;


-- =========================================================================
-- PARTE 3. LO QUE LA BASE NO CONTROLA (lo controla el PMV o el generador)
-- =========================================================================

-- 3.1 Capacidad: la base acepta más inscritos que cupos
START TRANSACTION;
UPDATE Excursiones SET Capacidad = 1 WHERE Registro_Codigo = 'EX-001';
SELECT x.Capacidad,
       (SELECT COUNT(*) FROM Inscripcion i WHERE i.Registro_Codigo = x.Registro_Codigo) AS Inscritos
FROM Excursiones x WHERE x.Registro_Codigo = 'EX-001';
ROLLBACK;

-- 3.2 Disjunción: la Araucaria (Vegetal) también entra en Especie_Mineral
START TRANSACTION;
INSERT INTO Especie_Mineral (Id_Especie, Roca, Cristales) VALUES (1, 'Granito', NULL);
SELECT e.Nombre_Vulgar, e.Tipo_Especie, m.Roca
FROM Especie e JOIN Especie_Mineral m ON m.Id_Especie = e.Id_Especie WHERE e.Id_Especie = 1;
ROLLBACK;


-- =========================================================================
-- PARTE 4. REQUERIMIENTOS: ¿QUÉ PASA SI CAMBIO LA CONSULTA?
-- =========================================================================

-- Ver el código de una vista o de un procedimiento
SHOW CREATE VIEW v_r3_visitantes_vs_evaluacion;
SHOW CREATE PROCEDURE sp_r9_excursiones_sobre_promedio;

-- R1 original (ene a mar): Sendero Alto 47 y Humedal 47
CALL sp_r1_areas_mas_visitantes('2026-01-01', '2026-03-31');

-- R1 sin WHERE Asistencia = 'Asiste': Sendero Alto 66 y Humedal 54
SELECT p.Nombre_Parque, a.Nombre_de_Area, COUNT(i.Id_Inscripcion) AS Visitantes
FROM Parque_Natural p
JOIN Area a        ON a.Anio_de_Declaracion = p.Anio_de_Declaracion
                  AND a.Numero_Correlativo  = p.Numero_Correlativo
JOIN Excursiones x ON x.Anio_de_Declaracion = a.Anio_de_Declaracion
                  AND x.Numero_Correlativo  = a.Numero_Correlativo
                  AND x.Numero_Interno      = a.Numero_Interno
JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
WHERE x.Fecha_Excursiones BETWEEN '2026-01-01' AND '2026-03-31'
GROUP BY p.Nombre_Parque, a.Nombre_de_Area
ORDER BY Visitantes DESC;

-- R1 con las fechas al revés: ninguna fila, sin error
CALL sp_r1_areas_mas_visitantes('2026-03-31', '2026-01-01');

-- R1 con un solo parámetro: error 1318
CALL sp_r1_areas_mas_visitantes('2026-01-01');

-- Columna fuera del GROUP BY: error 1055 (only_full_group_by)
SELECT p.Nombre_Parque, a.Nombre_de_Area, COUNT(*)
FROM Parque_Natural p
JOIN Area a ON a.Anio_de_Declaracion = p.Anio_de_Declaracion
           AND a.Numero_Correlativo  = p.Numero_Correlativo
GROUP BY p.Nombre_Parque;

-- R3 original: 159 excursiones y 929 visitantes
SELECT COUNT(*) AS Excursiones, SUM(Cantidad_Visitantes) AS Visitantes
FROM v_r3_visitantes_vs_evaluacion;

-- R3 con JOIN en vez de LEFT JOIN: 152 excursiones y 513 visitantes
SELECT COUNT(*) AS Excursiones, SUM(Visitantes) AS Visitantes
FROM (SELECT x.Registro_Codigo, COUNT(i.Id_Inscripcion) AS Visitantes
      FROM Excursiones x
      JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
      JOIN Evaluacion ev ON ev.Registro_Codigo = i.Registro_Codigo
                        AND ev.Id_Visitante    = i.Id_Visitante
      WHERE i.Asistencia = 'Asiste'
      GROUP BY x.Registro_Codigo) t;

-- R5 original: la tasa más baja es 45,71 %
SELECT MIN(Porcentaje_Asistencia) AS Tasa_Mas_Baja FROM v_r5_tasa_asistencia_area;

-- R5 sin excluir las Pendiente: la tasa más baja baja a 37,50 %
SELECT MIN(Porcentaje) AS Tasa_Mas_Baja
FROM (SELECT ROUND(SUM(CASE WHEN i.Asistencia = 'Asiste' THEN 1 ELSE 0 END) * 100 / COUNT(*), 2) AS Porcentaje
      FROM Area a
      JOIN Excursiones x ON x.Anio_de_Declaracion = a.Anio_de_Declaracion
                        AND x.Numero_Correlativo  = a.Numero_Correlativo
                        AND x.Numero_Interno      = a.Numero_Interno
      JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
      GROUP BY a.Anio_de_Declaracion, a.Numero_Correlativo, a.Numero_Interno) t;

-- R7 original: 21 proyectos, máximo 5 investigadores
SELECT COUNT(*) AS Proyectos, MAX(Cantidad_Investigadores) AS Max_Investigadores
FROM v_r7_proyectos_participacion;

-- R7 sin DISTINCT: el máximo sube a 20 (las filas se multiplican)
SELECT pc.Nombre_Proyecto, COUNT(per.Run) AS Investigadores, COUNT(e.Id_Especie) AS Especies
FROM Proyecto_Cientifico pc
JOIN Estudia es   ON es.Id_Proyecto = pc.Id_Proyecto
JOIN Personal per ON per.Run = es.Run
JOIN Investiga iv ON iv.Id_Proyecto = pc.Id_Proyecto
JOIN Especie e    ON e.Id_Especie = iv.Id_Especie
GROUP BY pc.Id_Proyecto, pc.Nombre_Proyecto
ORDER BY Investigadores DESC;

-- R8 original: 25 trabajadores con más de una función
SELECT COUNT(*) AS Trabajadores FROM v_r8_trabajadores_multifuncion;

-- R8 sin HAVING: 50 trabajadores
SELECT COUNT(DISTINCT Run) AS Trabajadores FROM Ejerce;

-- R8 sin DISTINCT en GROUP_CONCAT: las funciones se repiten
SELECT per.Run, GROUP_CONCAT(f.Nombre_Funcion) AS Funciones
FROM Personal per
JOIN Ejerce ej ON ej.Run = per.Run
JOIN Funcion f ON f.Id_Funcion = ej.Id_Funcion
GROUP BY per.Run
HAVING COUNT(*) > COUNT(DISTINCT f.Nombre_Funcion);

-- R9 original: 5 excursiones de Costa Rocosa sobre su promedio de 7,13
CALL sp_r9_excursiones_sobre_promedio('Parque Natural Costa Rocosa', '2026-01-01', '2026-10-31');

-- R9 con NULL: todos los parques, cada uno contra su propio promedio (74 filas)
CALL sp_r9_excursiones_sobre_promedio(NULL, '2026-01-01', '2026-10-31');

-- R9 sin correlación (contra el promedio general de 5,84): 9 excursiones
SELECT x.Registro_Codigo, COUNT(*) AS Visitantes
FROM Parque_Natural p
JOIN Excursiones x ON x.Anio_de_Declaracion = p.Anio_de_Declaracion
                  AND x.Numero_Correlativo  = p.Numero_Correlativo
JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
WHERE i.Asistencia = 'Asiste'
  AND p.Nombre_Parque = 'Parque Natural Costa Rocosa'
  AND x.Fecha_Excursiones BETWEEN '2026-01-01' AND '2026-10-31'
GROUP BY x.Registro_Codigo
HAVING COUNT(*) > (SELECT COUNT(i2.Id_Inscripcion) / COUNT(DISTINCT x2.Registro_Codigo)
                   FROM Excursiones x2
                   JOIN Inscripcion i2 ON i2.Registro_Codigo = x2.Registro_Codigo
                   WHERE i2.Asistencia = 'Asiste'
                     AND x2.Fecha_Excursiones BETWEEN '2026-01-01' AND '2026-10-31')
ORDER BY Visitantes DESC;

-- R10 con un tipo que no existe: ninguna fila, sin error
CALL sp_r10_especies_sobre_promedio_tipo('Hongo');

-- Los demás, tal como están
SELECT * FROM v_r2_distribucion_especies ORDER BY Nombre_Parque, Nombre_de_Area;
CALL sp_r4_parques_mas_excursiones('2026-01-01', '2026-10-31');
SELECT * FROM v_r6_especies_por_area ORDER BY Cantidad_Inventariada DESC;
CALL sp_r10_especies_sobre_promedio_tipo('Animal');
CALL sp_r11_visitantes_destacados('2026-01-01', '2026-10-31');
CALL sp_r12_parques_sobre_promedio('2026-01-01', '2026-10-31');


-- =========================================================================
-- PARTE 5. APOYO PARA LA DEMO DEL PMV (estas sí guardan cambios)
-- =========================================================================

-- Ver las últimas inscripciones (después de inscribir desde el PMV)
SELECT Id_Inscripcion, Registro_Codigo, Id_Visitante, Fecha_Inscripcion, Asistencia
FROM Inscripcion ORDER BY Id_Inscripcion DESC LIMIT 5;

-- Dejar llena la próxima excursión para mostrar el error de cupos
SET @exc = (SELECT Registro_Codigo FROM Excursiones
            WHERE Fecha_Excursiones >= CURDATE() ORDER BY Fecha_Excursiones LIMIT 1);
SET @cap = (SELECT Capacidad FROM Excursiones WHERE Registro_Codigo = @exc);
SELECT @exc AS Excursion, @cap AS Capacidad_Original;
UPDATE Excursiones
SET Capacidad = GREATEST(1, (SELECT COUNT(*) FROM Inscripcion i WHERE i.Registro_Codigo = @exc))
WHERE Registro_Codigo = @exc;
-- ... inscribir a alguien en esa excursión desde el PMV y ver el error ...
-- devolverle su capacidad
UPDATE Excursiones SET Capacidad = @cap WHERE Registro_Codigo = @exc;

-- Login: lo guardado es el hash, no la clave
SELECT Nombre_Usuario, Contrasena, SHA2('Admin2026!', 256) = Contrasena AS Coincide
FROM Usuario WHERE Nombre_Usuario = 'admin';

-- Cuentas que no pueden entrar (clave Parques2026!)
SELECT Nombre_Usuario, Estado_de_Cuenta FROM Usuario WHERE Estado_de_Cuenta <> 'Activa';

-- Roles de cada cuenta de demostración
SELECT u.Nombre_Usuario, r.Nombre_de_Rol
FROM Usuario u
JOIN Asignacion a  ON a.Id_Usuario = u.Id_Usuario
JOIN Rol_Sistema r ON r.Id_Rol = a.Id_Rol
WHERE u.Nombre_Usuario IN ('admin', 'operador', 'analista');
