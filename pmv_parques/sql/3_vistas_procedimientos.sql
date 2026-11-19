-- =========================================================================
-- 5. VISTAS (R2, R3, R5, R6, R7, R8)
--
-- Criterio común: un "visitante" de una excursión es una inscripción con
-- Asistencia = 'Asiste' (la persona efectivamente fue).
--
-- Recordatorio de cómo se unen las tablas con claves compuestas:
--   Parque_Natural (Anio, Correlativo)
--      -> Area (Anio, Correlativo, Numero_Interno)
--         -> Excursiones / Inventario_Especie (Anio, Correlativo, Numero_Interno)
-- =========================================================================
USE Sistema_Integral_Parques_Naturales;

-- -------------------------------------------------------------------------
-- R2: ¿Cómo se distribuyen las especies inventariadas entre vegetales,
--     animales y minerales, considerando parque y área?
-- -------------------------------------------------------------------------
CREATE VIEW v_r2_distribucion_especies AS
SELECT p.Nombre_Parque,
       a.Nombre_de_Area,
       IFNULL(e.Tipo_Especie, 'Sin clasificar') AS Tipo_Especie,
       COUNT(*)                                 AS Cantidad_Especies,
       SUM(i.Cantidad_Inventariada)             AS Total_Inventariado
FROM Inventario_Especie i
JOIN Especie e        ON e.Id_Especie = i.Id_Especie
JOIN Area a           ON a.Anio_de_Declaracion = i.Anio_de_Declaracion
                     AND a.Numero_Correlativo  = i.Numero_Correlativo
                     AND a.Numero_Interno      = i.Numero_Interno
JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                     AND p.Numero_Correlativo  = a.Numero_Correlativo
GROUP BY p.Nombre_Parque, a.Nombre_de_Area, e.Tipo_Especie;

-- -------------------------------------------------------------------------
-- R3: ¿Existe relación entre la cantidad de visitantes de una excursión
--     y su evaluación promedio?
-- LEFT JOIN con Evaluacion: no todos los visitantes dejan evaluación.
-- -------------------------------------------------------------------------
CREATE VIEW v_r3_visitantes_vs_evaluacion AS
SELECT x.Registro_Codigo,
       x.Fecha_Excursiones,
       p.Nombre_Parque,
       a.Nombre_de_Area,
       COUNT(i.Id_Inscripcion)        AS Cantidad_Visitantes,
       COUNT(ev.Calificacion)         AS Cantidad_Evaluaciones,
       ROUND(AVG(ev.Calificacion), 2) AS Promedio_Evaluacion
FROM Excursiones x
JOIN Area a           ON a.Anio_de_Declaracion = x.Anio_de_Declaracion
                     AND a.Numero_Correlativo  = x.Numero_Correlativo
                     AND a.Numero_Interno      = x.Numero_Interno
JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                     AND p.Numero_Correlativo  = a.Numero_Correlativo
JOIN Inscripcion i    ON i.Registro_Codigo = x.Registro_Codigo
LEFT JOIN Evaluacion ev ON ev.Registro_Codigo = i.Registro_Codigo
                       AND ev.Id_Visitante    = i.Id_Visitante
WHERE i.Asistencia = 'Asiste'
GROUP BY x.Registro_Codigo, x.Fecha_Excursiones, p.Nombre_Parque, a.Nombre_de_Area;

-- -------------------------------------------------------------------------
-- R5: ¿Qué áreas presentan mayor tasa de asistencia respecto de las
--     inscripciones realizadas?
-- Se excluyen las inscripciones 'Pendiente' (excursiones que aún no ocurren).
-- SUM(CASE ...) suma 1 por cada inscrito que asistió.
-- -------------------------------------------------------------------------
CREATE VIEW v_r5_tasa_asistencia_area AS
SELECT p.Nombre_Parque,
       a.Nombre_de_Area,
       COUNT(i.Id_Inscripcion)                                  AS Total_Inscritos,
       SUM(CASE WHEN i.Asistencia = 'Asiste' THEN 1 ELSE 0 END) AS Total_Asistentes,
       ROUND(SUM(CASE WHEN i.Asistencia = 'Asiste' THEN 1 ELSE 0 END) * 100
             / COUNT(i.Id_Inscripcion), 2)                      AS Porcentaje_Asistencia
FROM Parque_Natural p
JOIN Area a        ON a.Anio_de_Declaracion = p.Anio_de_Declaracion
                  AND a.Numero_Correlativo  = p.Numero_Correlativo
JOIN Excursiones x ON x.Anio_de_Declaracion = a.Anio_de_Declaracion
                  AND x.Numero_Correlativo  = a.Numero_Correlativo
                  AND x.Numero_Interno      = a.Numero_Interno
JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
WHERE i.Asistencia <> 'Pendiente'
GROUP BY p.Nombre_Parque, a.Nombre_de_Area;

-- -------------------------------------------------------------------------
-- R6: ¿Qué especies presentan mayor cantidad inventariada por parque y área?
-- La vista une las 4 tablas; al consultarla se ordena de mayor a menor.
-- -------------------------------------------------------------------------
CREATE VIEW v_r6_especies_por_area AS
SELECT p.Nombre_Parque,
       a.Nombre_de_Area,
       e.Nombre_Vulgar,
       e.Denominacion_Cientifica,
       IFNULL(e.Tipo_Especie, 'Sin clasificar') AS Tipo_Especie,
       i.Cantidad_Inventariada
FROM Inventario_Especie i
JOIN Especie e        ON e.Id_Especie = i.Id_Especie
JOIN Area a           ON a.Anio_de_Declaracion = i.Anio_de_Declaracion
                     AND a.Numero_Correlativo  = i.Numero_Correlativo
                     AND a.Numero_Interno      = i.Numero_Interno
JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                     AND p.Numero_Correlativo  = a.Numero_Correlativo;

-- -------------------------------------------------------------------------
-- R7: ¿Qué proyectos de investigación concentran mayor participación de
--     investigadores y especies estudiadas?
-- COUNT(DISTINCT ...) evita contar repetidos: al unir investigadores y
-- especies del mismo proyecto, las filas se multiplican.
-- HAVING deja solo proyectos con 2 o más investigadores.
-- -------------------------------------------------------------------------
CREATE VIEW v_r7_proyectos_participacion AS
SELECT pc.Nombre_Proyecto,
       pc.Estado,
       COUNT(DISTINCT per.Run)      AS Cantidad_Investigadores,
       COUNT(DISTINCT e.Id_Especie) AS Cantidad_Especies
FROM Proyecto_Cientifico pc
JOIN Estudia es   ON es.Id_Proyecto = pc.Id_Proyecto
JOIN Personal per ON per.Run = es.Run
JOIN Investiga iv ON iv.Id_Proyecto = pc.Id_Proyecto
JOIN Especie e    ON e.Id_Especie = iv.Id_Especie
GROUP BY pc.Nombre_Proyecto, pc.Estado
HAVING COUNT(DISTINCT per.Run) >= 2;

-- -------------------------------------------------------------------------
-- R8: ¿Qué trabajadores desempeñan más de una función y en qué parques o
--     áreas desarrollan sus actividades?
-- GROUP_CONCAT junta en un solo texto los valores del grupo (separados por coma).
-- -------------------------------------------------------------------------
CREATE VIEW v_r8_trabajadores_multifuncion AS
SELECT per.Run,
       CONCAT(per.Primer_Nombre, ' ', per.Apellido_Paterno)               AS Trabajador,
       per.Labores,
       COUNT(DISTINCT f.Nombre_Funcion)                                   AS Cantidad_Funciones,
       GROUP_CONCAT(DISTINCT f.Nombre_Funcion)                            AS Funciones,
       GROUP_CONCAT(DISTINCT CONCAT(p.Nombre_Parque, ' / ', a.Nombre_de_Area)) AS Parques_y_Areas
FROM Personal per
JOIN Ejerce ej        ON ej.Run = per.Run
JOIN Funcion f        ON f.Id_Funcion = ej.Id_Funcion
JOIN Area a           ON a.Anio_de_Declaracion = ej.Anio_de_Declaracion
                     AND a.Numero_Correlativo  = ej.Numero_Correlativo
                     AND a.Numero_Interno      = ej.Numero_Interno
JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                     AND p.Numero_Correlativo  = a.Numero_Correlativo
GROUP BY per.Run, per.Primer_Nombre, per.Apellido_Paterno, per.Labores
HAVING COUNT(DISTINCT f.Nombre_Funcion) > 1;


-- =========================================================================
-- 6. PROCEDIMIENTOS ALMACENADOS (R1, R4, R9, R10, R11, R12)
-- DELIMITER cambia el fin de sentencia a $$ para poder escribir ; dentro
-- del procedimiento.
-- =========================================================================
DELIMITER $$

-- -------------------------------------------------------------------------
-- R1: ¿Cuáles son las áreas con mayor cantidad de visitantes mediante
--     excursiones durante un período determinado?
-- Ejemplo: CALL sp_r1_areas_mas_visitantes('2026-01-01', '2026-03-31');
-- -------------------------------------------------------------------------
CREATE PROCEDURE sp_r1_areas_mas_visitantes(IN p_fecha_inicio DATE, IN p_fecha_termino DATE)
BEGIN
    SELECT p.Nombre_Parque,
           a.Nombre_de_Area,
           COUNT(DISTINCT x.Registro_Codigo) AS Excursiones,
           COUNT(i.Id_Inscripcion)           AS Visitantes
    FROM Parque_Natural p
    JOIN Area a        ON a.Anio_de_Declaracion = p.Anio_de_Declaracion
                      AND a.Numero_Correlativo  = p.Numero_Correlativo
    JOIN Excursiones x ON x.Anio_de_Declaracion = a.Anio_de_Declaracion
                      AND x.Numero_Correlativo  = a.Numero_Correlativo
                      AND x.Numero_Interno      = a.Numero_Interno
    JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
    WHERE i.Asistencia = 'Asiste'
      AND x.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino
    GROUP BY p.Nombre_Parque, a.Nombre_de_Area
    ORDER BY Visitantes DESC;
END$$

-- -------------------------------------------------------------------------
-- R4: ¿Qué parques concentran la mayor cantidad de excursiones y visitantes
--     en un período determinado?
-- Ejemplo: CALL sp_r4_parques_mas_excursiones('2026-01-01', '2026-10-31');
-- -------------------------------------------------------------------------
CREATE PROCEDURE sp_r4_parques_mas_excursiones(IN p_fecha_inicio DATE, IN p_fecha_termino DATE)
BEGIN
    SELECT p.Nombre_Parque,
           COUNT(DISTINCT x.Registro_Codigo) AS Excursiones,
           COUNT(i.Id_Inscripcion)           AS Visitantes
    FROM Parque_Natural p
    JOIN Area a        ON a.Anio_de_Declaracion = p.Anio_de_Declaracion
                      AND a.Numero_Correlativo  = p.Numero_Correlativo
    JOIN Excursiones x ON x.Anio_de_Declaracion = a.Anio_de_Declaracion
                      AND x.Numero_Correlativo  = a.Numero_Correlativo
                      AND x.Numero_Interno      = a.Numero_Interno
    JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
    WHERE i.Asistencia = 'Asiste'
      AND x.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino
    GROUP BY p.Nombre_Parque
    ORDER BY Excursiones DESC, Visitantes DESC;
END$$

-- -------------------------------------------------------------------------
-- R9: ¿Qué excursiones superan el promedio de visitantes de las excursiones
--     realizadas en el mismo parque?
-- Parámetros: nombre del parque (NULL = todos los parques) y período.
-- La subconsulta es CORRELACIONADA: usa x.Anio_de_Declaracion y
-- x.Numero_Correlativo de la consulta externa, así calcula el promedio del
-- parque de CADA excursión.
-- Promedio de visitantes por excursión = total de visitantes / cantidad de excursiones.
-- Ejemplo: CALL sp_r9_excursiones_sobre_promedio('Parque Natural Costa Rocosa', '2026-01-01', '2026-10-31');
--          CALL sp_r9_excursiones_sobre_promedio(NULL, '2026-01-01', '2026-10-31');
-- -------------------------------------------------------------------------
CREATE PROCEDURE sp_r9_excursiones_sobre_promedio(IN p_parque VARCHAR(80),
                                                  IN p_fecha_inicio DATE, IN p_fecha_termino DATE)
BEGIN
    SELECT p.Nombre_Parque,
           a.Nombre_de_Area,
           x.Registro_Codigo,
           x.Fecha_Excursiones,
           COUNT(i.Id_Inscripcion) AS Visitantes,
           (SELECT ROUND(COUNT(i2.Id_Inscripcion) / COUNT(DISTINCT x2.Registro_Codigo), 2)
            FROM Excursiones x2
            JOIN Inscripcion i2 ON i2.Registro_Codigo = x2.Registro_Codigo
            WHERE i2.Asistencia = 'Asiste'
              AND x2.Anio_de_Declaracion = x.Anio_de_Declaracion
              AND x2.Numero_Correlativo  = x.Numero_Correlativo
              AND x2.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino) AS Promedio_del_Parque
    FROM Parque_Natural p
    JOIN Area a        ON a.Anio_de_Declaracion = p.Anio_de_Declaracion
                      AND a.Numero_Correlativo  = p.Numero_Correlativo
    JOIN Excursiones x ON x.Anio_de_Declaracion = a.Anio_de_Declaracion
                      AND x.Numero_Correlativo  = a.Numero_Correlativo
                      AND x.Numero_Interno      = a.Numero_Interno
    JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
    WHERE i.Asistencia = 'Asiste'
      AND (p_parque IS NULL OR p.Nombre_Parque = p_parque)
      AND x.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino
    GROUP BY p.Nombre_Parque, a.Nombre_de_Area, x.Registro_Codigo, x.Fecha_Excursiones,
             x.Anio_de_Declaracion, x.Numero_Correlativo
    HAVING COUNT(i.Id_Inscripcion) >
           (SELECT COUNT(i2.Id_Inscripcion) / COUNT(DISTINCT x2.Registro_Codigo)
            FROM Excursiones x2
            JOIN Inscripcion i2 ON i2.Registro_Codigo = x2.Registro_Codigo
            WHERE i2.Asistencia = 'Asiste'
              AND x2.Anio_de_Declaracion = x.Anio_de_Declaracion
              AND x2.Numero_Correlativo  = x.Numero_Correlativo
              AND x2.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino)
    ORDER BY p.Nombre_Parque, Visitantes DESC;
END$$

-- -------------------------------------------------------------------------
-- R10: ¿Qué especies poseen una cantidad inventariada superior al promedio
--      de las especies de su mismo tipo?
-- Parámetro: tipo de especie ('Vegetal', 'Animal' o 'Mineral').
-- Cantidad de una especie = suma de lo inventariado en todas sus áreas.
-- Promedio del tipo = total inventariado del tipo / cantidad de especies del tipo.
-- Ejemplo: CALL sp_r10_especies_sobre_promedio_tipo('Animal');
-- -------------------------------------------------------------------------
CREATE PROCEDURE sp_r10_especies_sobre_promedio_tipo(IN p_tipo VARCHAR(10))
BEGIN
    SELECT e.Nombre_Vulgar,
           e.Denominacion_Cientifica,
           e.Tipo_Especie,
           COUNT(DISTINCT p.Nombre_Parque) AS Parques,
           COUNT(*)                        AS Areas,
           SUM(i.Cantidad_Inventariada)    AS Total_Inventariado,
           (SELECT ROUND(SUM(i2.Cantidad_Inventariada) / COUNT(DISTINCT i2.Id_Especie), 2)
            FROM Inventario_Especie i2
            JOIN Especie e2 ON e2.Id_Especie = i2.Id_Especie
            WHERE e2.Tipo_Especie = p_tipo) AS Promedio_del_Tipo
    FROM Especie e
    JOIN Inventario_Especie i ON i.Id_Especie = e.Id_Especie
    JOIN Area a               ON a.Anio_de_Declaracion = i.Anio_de_Declaracion
                             AND a.Numero_Correlativo  = i.Numero_Correlativo
                             AND a.Numero_Interno      = i.Numero_Interno
    JOIN Parque_Natural p     ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                             AND p.Numero_Correlativo  = a.Numero_Correlativo
    WHERE e.Tipo_Especie = p_tipo
    GROUP BY e.Id_Especie, e.Nombre_Vulgar, e.Denominacion_Cientifica, e.Tipo_Especie
    HAVING SUM(i.Cantidad_Inventariada) >
           (SELECT SUM(i2.Cantidad_Inventariada) / COUNT(DISTINCT i2.Id_Especie)
            FROM Inventario_Especie i2
            JOIN Especie e2 ON e2.Id_Especie = i2.Id_Especie
            WHERE e2.Tipo_Especie = p_tipo)
    ORDER BY Total_Inventariado DESC;
END$$

-- -------------------------------------------------------------------------
-- R11: ¿Qué visitantes han participado en más excursiones que el promedio
--      y además poseen una evaluación promedio superior al promedio general?
-- Parámetros: rango de fechas.
-- Promedio de excursiones por visitante = asistencias / visitantes distintos.
-- Ejemplo: CALL sp_r11_visitantes_destacados('2026-01-01', '2026-10-31');
-- -------------------------------------------------------------------------
CREATE PROCEDURE sp_r11_visitantes_destacados(IN p_fecha_inicio DATE, IN p_fecha_termino DATE)
BEGIN
    SELECT v.Id_Visitante,
           v.Nombre_Visitante,
           COUNT(i.Id_Inscripcion)        AS Excursiones_Participadas,
           ROUND(AVG(ev.Calificacion), 2) AS Evaluacion_Promedio
    FROM Visitantes v
    JOIN Inscripcion i ON i.Id_Visitante = v.Id_Visitante
    JOIN Excursiones x ON x.Registro_Codigo = i.Registro_Codigo
    LEFT JOIN Evaluacion ev ON ev.Registro_Codigo = i.Registro_Codigo
                           AND ev.Id_Visitante    = i.Id_Visitante
    WHERE i.Asistencia = 'Asiste'
      AND x.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino
    GROUP BY v.Id_Visitante, v.Nombre_Visitante
    HAVING COUNT(i.Id_Inscripcion) >
               (SELECT COUNT(i2.Id_Inscripcion) / COUNT(DISTINCT i2.Id_Visitante)
                FROM Inscripcion i2
                JOIN Excursiones x2 ON x2.Registro_Codigo = i2.Registro_Codigo
                WHERE i2.Asistencia = 'Asiste'
                  AND x2.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino)
       AND AVG(ev.Calificacion) >
               (SELECT AVG(ev3.Calificacion)
                FROM Evaluacion ev3
                JOIN Excursiones x3 ON x3.Registro_Codigo = ev3.Registro_Codigo
                WHERE x3.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino)
    ORDER BY Excursiones_Participadas DESC, Evaluacion_Promedio DESC;
END$$

-- -------------------------------------------------------------------------
-- R12: ¿Qué parques presentan un promedio de visitantes por excursión superior
--      al promedio general de los parques durante un período?
-- Promedio general = total de visitantes / total de excursiones del período.
-- Ejemplo: CALL sp_r12_parques_sobre_promedio('2026-01-01', '2026-10-31');
-- -------------------------------------------------------------------------
CREATE PROCEDURE sp_r12_parques_sobre_promedio(IN p_fecha_inicio DATE, IN p_fecha_termino DATE)
BEGIN
    SELECT p.Nombre_Parque,
           COUNT(DISTINCT x.Registro_Codigo) AS Excursiones,
           COUNT(i.Id_Inscripcion)           AS Visitantes,
           ROUND(COUNT(i.Id_Inscripcion) / COUNT(DISTINCT x.Registro_Codigo), 2) AS Promedio_del_Parque,
           (SELECT ROUND(COUNT(i2.Id_Inscripcion) / COUNT(DISTINCT x2.Registro_Codigo), 2)
            FROM Excursiones x2
            JOIN Inscripcion i2 ON i2.Registro_Codigo = x2.Registro_Codigo
            WHERE i2.Asistencia = 'Asiste'
              AND x2.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino) AS Promedio_General
    FROM Parque_Natural p
    JOIN Area a        ON a.Anio_de_Declaracion = p.Anio_de_Declaracion
                      AND a.Numero_Correlativo  = p.Numero_Correlativo
    JOIN Excursiones x ON x.Anio_de_Declaracion = a.Anio_de_Declaracion
                      AND x.Numero_Correlativo  = a.Numero_Correlativo
                      AND x.Numero_Interno      = a.Numero_Interno
    JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
    WHERE i.Asistencia = 'Asiste'
      AND x.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino
    GROUP BY p.Nombre_Parque
    HAVING COUNT(i.Id_Inscripcion) / COUNT(DISTINCT x.Registro_Codigo) >
           (SELECT COUNT(i2.Id_Inscripcion) / COUNT(DISTINCT x2.Registro_Codigo)
            FROM Excursiones x2
            JOIN Inscripcion i2 ON i2.Registro_Codigo = x2.Registro_Codigo
            WHERE i2.Asistencia = 'Asiste'
              AND x2.Fecha_Excursiones BETWEEN p_fecha_inicio AND p_fecha_termino)
    ORDER BY Promedio_del_Parque DESC;
END$$

DELIMITER ;

-- =========================================================================
-- SENTENCIAS PARA PROBAR (usar en Workbench para las capturas del informe)
-- =========================================================================
-- SELECT * FROM v_r2_distribucion_especies ORDER BY Nombre_Parque, Nombre_de_Area;
-- SELECT * FROM v_r3_visitantes_vs_evaluacion ORDER BY Cantidad_Visitantes DESC;
-- SELECT * FROM v_r5_tasa_asistencia_area ORDER BY Porcentaje_Asistencia DESC;
-- SELECT * FROM v_r6_especies_por_area ORDER BY Nombre_Parque, Nombre_de_Area, Cantidad_Inventariada DESC;
-- SELECT * FROM v_r7_proyectos_participacion ORDER BY Cantidad_Investigadores DESC, Cantidad_Especies DESC;
-- SELECT * FROM v_r8_trabajadores_multifuncion ORDER BY Cantidad_Funciones DESC;
-- CALL sp_r1_areas_mas_visitantes('2026-01-01', '2026-03-31');
-- CALL sp_r4_parques_mas_excursiones('2026-01-01', '2026-10-31');
-- CALL sp_r9_excursiones_sobre_promedio('Parque Natural Costa Rocosa', '2026-01-01', '2026-10-31');
-- CALL sp_r10_especies_sobre_promedio_tipo('Animal');
-- CALL sp_r11_visitantes_destacados('2026-01-01', '2026-10-31');
-- CALL sp_r12_parques_sobre_promedio('2026-01-01', '2026-10-31');
