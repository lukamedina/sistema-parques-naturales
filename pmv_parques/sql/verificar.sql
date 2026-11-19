-- verificar.sql: muestra que el script integral creó la base completa.
-- Uso (con docker compose levantado):
--   docker compose exec db mysql -uroot -pParques2026 -t -e "source /verificar.sql"
-- En Workbench también se puede abrir y ejecutar completo.

USE Sistema_Integral_Parques_Naturales;

-- 1) Cuántas filas tiene cada tabla principal
SELECT 'Comunidad_Autonoma' AS Tabla, COUNT(*) AS Filas FROM Comunidad_Autonoma
UNION ALL SELECT 'Parque_Natural', COUNT(*) FROM Parque_Natural
UNION ALL SELECT 'Area', COUNT(*) FROM Area
UNION ALL SELECT 'Especie', COUNT(*) FROM Especie
UNION ALL SELECT 'Inventario_Especie', COUNT(*) FROM Inventario_Especie
UNION ALL SELECT 'Personal', COUNT(*) FROM Personal
UNION ALL SELECT 'Proyecto_Cientifico', COUNT(*) FROM Proyecto_Cientifico
UNION ALL SELECT 'Visitantes', COUNT(*) FROM Visitantes
UNION ALL SELECT 'Excursiones', COUNT(*) FROM Excursiones
UNION ALL SELECT 'Inscripcion', COUNT(*) FROM Inscripcion
UNION ALL SELECT 'Evaluacion', COUNT(*) FROM Evaluacion
UNION ALL SELECT 'Usuario', COUNT(*) FROM Usuario;

-- 2) Cuántos objetos creó el script
SELECT
    (SELECT COUNT(*) FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = 'Sistema_Integral_Parques_Naturales' AND TABLE_TYPE = 'BASE TABLE') AS Tablas,
    (SELECT COUNT(*) FROM information_schema.VIEWS
     WHERE TABLE_SCHEMA = 'Sistema_Integral_Parques_Naturales') AS Vistas,
    (SELECT COUNT(*) FROM information_schema.ROUTINES
     WHERE ROUTINE_SCHEMA = 'Sistema_Integral_Parques_Naturales' AND ROUTINE_TYPE = 'PROCEDURE') AS Procedimientos;
