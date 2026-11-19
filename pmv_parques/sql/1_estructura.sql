-- =========================================================================
-- PROYECTO SEMESTRAL 2026 - TDFI103 BASES DE DATOS - FASE 2 - GRUPO 8
-- Caso 1: Sistema Integral de Gestión de Parques Naturales y Conservación Ambiental
--
-- SCRIPT INTEGRAL
--   1. Creación de la base de datos
--   2. Creación de tablas
--   3. Restricciones, claves y relaciones (PK, FK, NOT NULL, UNIQUE, CHECK)
--   4. Inserción de datos (generados con generador/generar_datos.py)
--   5. Creación de 6 vistas
--   6. Creación de 6 procedimientos almacenados
--
-- Motor: MySQL 8.0.16 o superior (desde esa versión se respetan los CHECK).
-- Se ejecuta completo de principio a fin y reconstruye la base desde cero.
--
-- Tipos de datos usados (solo tipos básicos):
--   INT, DECIMAL, VARCHAR, DATE y TIME.
--   Los valores "sí/no" se guardan como texto: 'Si' o 'No'.
-- =========================================================================

SET NAMES utf8mb4;   -- para que se guarden bien las tildes y la ñ

-- -------------------------------------------------------------------------
-- 1. CREACIÓN DE LA BASE DE DATOS
-- -------------------------------------------------------------------------
DROP DATABASE IF EXISTS Sistema_Integral_Parques_Naturales;
CREATE DATABASE Sistema_Integral_Parques_Naturales;
USE Sistema_Integral_Parques_Naturales;

-- =========================================================================
-- 2 y 3. TABLAS CON SUS RESTRICCIONES
-- =========================================================================

-- ---------------- MÓDULO 1: COMUNIDADES, PARQUES Y ÁREAS -----------------

CREATE TABLE Comunidad_Autonoma (
    Codigo                VARCHAR(10)  NOT NULL,
    Nombre_Comunidad      VARCHAR(100) NOT NULL,
    Region_Administrativa VARCHAR(100) NOT NULL,
    Organismo_Responsable VARCHAR(150) NOT NULL,
    PRIMARY KEY (Codigo),
    UNIQUE (Nombre_Comunidad)
);

-- El parque se identifica por un ROL compuesto: año de declaración + número correlativo.
-- Codigo_Comunidad es la comunidad principal responsable (todo parque debe tener una).
-- Activo = 'No' significa que el parque fue desactivado desde el PMV (eliminación lógica).
CREATE TABLE Parque_Natural (
    Anio_de_Declaracion    INT           NOT NULL,
    Numero_Correlativo     INT           NOT NULL,
    Nombre_Parque          VARCHAR(80)   NOT NULL,
    Fecha_de_Declaracion   DATE          NOT NULL,
    Superficie_Total       DECIMAL(12,2) NOT NULL,   -- en hectáreas
    Presupuesto_Anual      DECIMAL(14,2) NOT NULL,   -- en pesos
    Estado_de_Conservacion VARCHAR(10)   NOT NULL,
    Ubicacion              VARCHAR(80)   NOT NULL,
    Activo                 VARCHAR(2)    NOT NULL DEFAULT 'Si',
    Codigo_Comunidad       VARCHAR(10)   NOT NULL,
    PRIMARY KEY (Anio_de_Declaracion, Numero_Correlativo),
    UNIQUE (Nombre_Parque),
    CHECK (Anio_de_Declaracion >= 1900),
    CHECK (Numero_Correlativo > 0),
    CHECK (Anio_de_Declaracion = YEAR(Fecha_de_Declaracion)),
    CHECK (Superficie_Total > 0),
    CHECK (Presupuesto_Anual > 0),
    CHECK (Estado_de_Conservacion IN ('Bueno', 'Regular', 'Critico')),
    CHECK (Activo IN ('Si', 'No')),
    FOREIGN KEY (Codigo_Comunidad) REFERENCES Comunidad_Autonoma (Codigo)
);

-- Relación N:M "PARTICIPA": un parque puede estar compartido por varias comunidades.
CREATE TABLE Participacion_Comunidad (
    Codigo_Comunidad       VARCHAR(10)  NOT NULL,
    Anio_de_Declaracion    INT          NOT NULL,
    Numero_Correlativo     INT          NOT NULL,
    Porcentaje_Territorial DECIMAL(5,2) NOT NULL,
    PRIMARY KEY (Codigo_Comunidad, Anio_de_Declaracion, Numero_Correlativo),
    CHECK (Porcentaje_Territorial > 0 AND Porcentaje_Territorial <= 100),
    FOREIGN KEY (Codigo_Comunidad) REFERENCES Comunidad_Autonoma (Codigo),
    FOREIGN KEY (Anio_de_Declaracion, Numero_Correlativo)
        REFERENCES Parque_Natural (Anio_de_Declaracion, Numero_Correlativo)
);

-- ÁREA es entidad DÉBIL de Parque_Natural:
-- su PK es la PK del parque + el número interno (único solo dentro del parque).
CREATE TABLE Area (
    Anio_de_Declaracion INT           NOT NULL,
    Numero_Correlativo  INT           NOT NULL,
    Numero_Interno      INT           NOT NULL,
    Nombre_de_Area      VARCHAR(40)   NOT NULL,
    Extension           DECIMAL(10,2) NOT NULL,   -- en hectáreas
    Nivel_Acceso        VARCHAR(20)   NOT NULL,
    Estado_Operativo    VARCHAR(20)   NOT NULL,
    PRIMARY KEY (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno),
    UNIQUE (Anio_de_Declaracion, Numero_Correlativo, Nombre_de_Area),  -- no hay dos áreas con el mismo nombre en un parque
    CHECK (Numero_Interno > 0),
    CHECK (Extension > 0),
    CHECK (Nivel_Acceso IN ('Libre', 'Restringido', 'Solo Investigacion')),
    CHECK (Estado_Operativo IN ('Operativa', 'Mantencion', 'Cerrada')),
    FOREIGN KEY (Anio_de_Declaracion, Numero_Correlativo)
        REFERENCES Parque_Natural (Anio_de_Declaracion, Numero_Correlativo)
);

-- ---------------- MÓDULO 2: ESPECIES E INVENTARIO ------------------------

-- Generalización ESPECIE -> VEGETAL / ANIMAL / MINERAL
--   * DISJUNTA: una especie clasificada pertenece a un solo subtipo.
--   * PARCIAL : puede haber especies sin clasificar (Tipo_Especie = NULL),
--               por ejemplo hongos, líquenes y algas.
-- Tipo_Especie es el atributo DISCRIMINADOR.
CREATE TABLE Especie (
    Id_Especie              INT          NOT NULL AUTO_INCREMENT,
    Denominacion_Cientifica VARCHAR(150) NOT NULL,
    Nombre_Vulgar           VARCHAR(80)  NOT NULL,
    Estado_de_Conservacion  VARCHAR(30)  NOT NULL,
    Fecha_Especie           DATE         NOT NULL,   -- fecha de incorporación al inventario
    Tipo_Especie            VARCHAR(10)  NULL,
    Activo                  VARCHAR(2)   NOT NULL DEFAULT 'Si',
    PRIMARY KEY (Id_Especie),
    UNIQUE (Denominacion_Cientifica),
    CHECK (Estado_de_Conservacion IN ('Preocupacion Menor', 'Casi Amenazada', 'Vulnerable',
                                      'En Peligro', 'Peligro Critico')),
    CHECK (Tipo_Especie IN ('Vegetal', 'Animal', 'Mineral')),
    CHECK (Activo IN ('Si', 'No'))
);

-- Subtipos: su PK es también FK hacia Especie (transformación clásica de la jerarquía).
CREATE TABLE Especie_Vegetal (
    Id_Especie             INT          NOT NULL,
    Antecedentes_Floracion VARCHAR(100) NOT NULL,
    PRIMARY KEY (Id_Especie),
    FOREIGN KEY (Id_Especie) REFERENCES Especie (Id_Especie)
);

CREATE TABLE Especie_Animal (
    Id_Especie   INT         NOT NULL,
    Alimentacion VARCHAR(20) NOT NULL,
    Periodo_Celo VARCHAR(20) NOT NULL,
    PRIMARY KEY (Id_Especie),
    CHECK (Alimentacion IN ('Herbivoro', 'Carnivoro', 'Omnivoro', 'Insectivoro', 'Carronero', 'Piscivoro')),
    CHECK (Periodo_Celo IN ('Verano', 'Otono', 'Invierno', 'Primavera', 'Anual')),
    FOREIGN KEY (Id_Especie) REFERENCES Especie (Id_Especie)
);

CREATE TABLE Especie_Mineral (
    Id_Especie INT         NOT NULL,
    Roca       VARCHAR(50) NULL,
    Cristales  VARCHAR(50) NULL,
    PRIMARY KEY (Id_Especie),
    CHECK (Roca IS NOT NULL OR Cristales IS NOT NULL),   -- debe tener al menos uno de los dos
    FOREIGN KEY (Id_Especie) REFERENCES Especie (Id_Especie)
);

-- INVENTARIO_ESPECIE: entidad ASOCIATIVA entre Área y Especie (N:M con atributos propios).
CREATE TABLE Inventario_Especie (
    Anio_de_Declaracion        INT          NOT NULL,
    Numero_Correlativo         INT          NOT NULL,
    Numero_Interno             INT          NOT NULL,
    Id_Especie                 INT          NOT NULL,
    Cantidad_Inventariada      INT          NOT NULL,
    Fecha_Ultimo_Monitoreo     DATE         NOT NULL,
    Observaciones_Inventariado VARCHAR(150) NULL,
    PRIMARY KEY (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno, Id_Especie),
    CHECK (Cantidad_Inventariada > 0),
    FOREIGN KEY (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno)
        REFERENCES Area (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno),
    FOREIGN KEY (Id_Especie) REFERENCES Especie (Id_Especie)
);

-- ---------------- MÓDULO 3: EXCURSIONES, VISITANTES, INSCRIPCIONES -------

CREATE TABLE Excursiones (
    Registro_Codigo     VARCHAR(10) NOT NULL,
    Fecha_Excursiones   DATE        NOT NULL,
    Horario_Excursiones TIME        NOT NULL,
    Modalidad           VARCHAR(30) NOT NULL,
    Capacidad           INT         NOT NULL,
    Anio_de_Declaracion INT         NOT NULL,
    Numero_Correlativo  INT         NOT NULL,
    Numero_Interno      INT         NOT NULL,
    PRIMARY KEY (Registro_Codigo),
    CHECK (Modalidad IN ('Senderismo', 'Observacion de Fauna', 'Observacion Botanica',
                         'Geologia', 'Fotografia', 'Educativa')),
    CHECK (Capacidad BETWEEN 1 AND 500),
    FOREIGN KEY (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno)
        REFERENCES Area (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno)
);

CREATE TABLE Visitantes (
    Id_Visitante       VARCHAR(10)  NOT NULL,
    Nombre_Visitante   VARCHAR(80)  NOT NULL,
    Correo_Electronico VARCHAR(100) NOT NULL,
    PRIMARY KEY (Id_Visitante),
    UNIQUE (Correo_Electronico)
);

-- INSCRIPCIÓN: entidad ASOCIATIVA entre Visitante y Excursión.
-- Asistencia: 'Pendiente' (la excursión aún no se realiza), 'Asiste' o 'No Asiste'.
-- El UNIQUE impide que un visitante se inscriba dos veces en la misma excursión.
CREATE TABLE Inscripcion (
    Id_Inscripcion    INT          NOT NULL AUTO_INCREMENT,
    Registro_Codigo   VARCHAR(10)  NOT NULL,
    Id_Visitante      VARCHAR(10)  NOT NULL,
    Fecha_Inscripcion DATE         NOT NULL,
    Asistencia        VARCHAR(10)  NOT NULL DEFAULT 'Pendiente',
    Observaciones     VARCHAR(100) NULL,
    PRIMARY KEY (Id_Inscripcion),
    UNIQUE (Registro_Codigo, Id_Visitante),
    CHECK (Asistencia IN ('Pendiente', 'Asiste', 'No Asiste')),
    FOREIGN KEY (Registro_Codigo) REFERENCES Excursiones (Registro_Codigo),
    FOREIGN KEY (Id_Visitante)    REFERENCES Visitantes (Id_Visitante)
);

-- EVALUACIÓN: entidad DÉBIL de Excursiones (número correlativo dentro de cada excursión).
-- El UNIQUE asegura que cada visitante evalúa una sola vez cada excursión.
CREATE TABLE Evaluacion (
    Registro_Codigo   VARCHAR(10)  NOT NULL,
    Numero_Evaluacion INT          NOT NULL,
    Id_Visitante      VARCHAR(10)  NOT NULL,
    Fecha_Evaluacion  DATE         NOT NULL,
    Calificacion      INT          NOT NULL,
    Comentario        VARCHAR(500) NULL,       -- comentario opcional
    PRIMARY KEY (Registro_Codigo, Numero_Evaluacion),
    UNIQUE (Registro_Codigo, Id_Visitante),
    CHECK (Numero_Evaluacion > 0),
    CHECK (Calificacion BETWEEN 1 AND 7),
    FOREIGN KEY (Registro_Codigo) REFERENCES Excursiones (Registro_Codigo),
    FOREIGN KEY (Id_Visitante)    REFERENCES Visitantes (Id_Visitante)
);

-- ---------------- MÓDULO 4: PERSONAL, FUNCIONES, USUARIOS Y ROLES -------

-- Nombre (Primer_Nombre + apellidos) y Dirección (Calle + Numero + Region) son
-- atributos COMPUESTOS. La edad es DERIVADA (se calcula con la fecha de nacimiento).
-- El correo es OPCIONAL (puede ser NULL).
CREATE TABLE Personal (
    Run                     VARCHAR(12)  NOT NULL,
    Primer_Nombre           VARCHAR(40)  NOT NULL,
    Apellido_Paterno        VARCHAR(40)  NOT NULL,
    Apellido_Materno        VARCHAR(40)  NOT NULL,
    Fecha_Nacimiento        DATE         NOT NULL,
    Antecedentes_Personales VARCHAR(255) NULL,
    Labores                 VARCHAR(60)  NOT NULL,   -- cargo
    Calle                   VARCHAR(60)  NOT NULL,
    Numero                  INT          NOT NULL,
    Region                  VARCHAR(60)  NOT NULL,
    Correo_Electronico      VARCHAR(100) NULL,
    PRIMARY KEY (Run),
    UNIQUE (Correo_Electronico),
    CHECK (Numero > 0)
);

-- CONTACTO: atributo MULTIVALUADO de Personal (una persona puede tener varios teléfonos).
CREATE TABLE Contacto (
    Run      VARCHAR(12) NOT NULL,
    Contacto VARCHAR(30) NOT NULL,
    PRIMARY KEY (Run, Contacto),
    FOREIGN KEY (Run) REFERENCES Personal (Run)
);

-- Especialización de PERSONAL -> TRABAJADOR / INVESTIGADOR (SOLAPADA:
-- una misma persona puede ser trabajador e investigador a la vez).
-- Run_Supervisor es la relación UNARIA "SUPERVISA" (1:N).
CREATE TABLE Trabajadores (
    Run            VARCHAR(12) NOT NULL,
    Run_Supervisor VARCHAR(12) NULL,
    PRIMARY KEY (Run),
    CHECK (Run_Supervisor IS NULL OR Run_Supervisor <> Run),   -- nadie se supervisa a sí mismo
    FOREIGN KEY (Run)            REFERENCES Personal (Run),
    FOREIGN KEY (Run_Supervisor) REFERENCES Trabajadores (Run)
);

CREATE TABLE Investigacion (
    Run VARCHAR(12) NOT NULL,
    PRIMARY KEY (Run),
    FOREIGN KEY (Run) REFERENCES Personal (Run)
);

-- Funciones posibles: Gestión, Vigilancia, Conservación, Investigación.
CREATE TABLE Funcion (
    Id_Funcion     INT         NOT NULL,
    Nombre_Funcion VARCHAR(40) NOT NULL,
    PRIMARY KEY (Id_Funcion),
    UNIQUE (Nombre_Funcion)
);

-- EJERCE: qué función cumple cada trabajador y en qué área (un trabajador puede tener varias).
CREATE TABLE Ejerce (
    Run                 VARCHAR(12) NOT NULL,
    Id_Funcion          INT         NOT NULL,
    Anio_de_Declaracion INT         NOT NULL,
    Numero_Correlativo  INT         NOT NULL,
    Numero_Interno      INT         NOT NULL,
    Fecha_Inicio        DATE        NOT NULL,
    PRIMARY KEY (Run, Id_Funcion, Anio_de_Declaracion, Numero_Correlativo, Numero_Interno),
    FOREIGN KEY (Run)        REFERENCES Trabajadores (Run),
    FOREIGN KEY (Id_Funcion) REFERENCES Funcion (Id_Funcion),
    FOREIGN KEY (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno)
        REFERENCES Area (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno)
);

CREATE TABLE Rol_Sistema (
    Id_Rol        INT         NOT NULL,
    Nombre_de_Rol VARCHAR(40) NOT NULL,
    PRIMARY KEY (Id_Rol),
    UNIQUE (Nombre_de_Rol)
);

-- USUARIO: relación 1:1 con Personal (Run es UNIQUE).
-- La contraseña NO se guarda en texto plano: se guarda el resultado de SHA2(clave, 256).
CREATE TABLE Usuario (
    Id_Usuario       INT         NOT NULL,
    Run              VARCHAR(12) NOT NULL,
    Nombre_Usuario   VARCHAR(30) NOT NULL,
    Contrasena       VARCHAR(64) NOT NULL,
    Estado_de_Cuenta VARCHAR(10) NOT NULL,
    PRIMARY KEY (Id_Usuario),
    UNIQUE (Run),
    UNIQUE (Nombre_Usuario),
    CHECK (Estado_de_Cuenta IN ('Activa', 'Inactiva', 'Suspendida')),
    FOREIGN KEY (Run) REFERENCES Personal (Run)
);

-- ASIGNACIÓN: relación N:M entre Usuario y Rol (un usuario puede tener varios roles).
CREATE TABLE Asignacion (
    Id_Usuario INT NOT NULL,
    Id_Rol     INT NOT NULL,
    PRIMARY KEY (Id_Usuario, Id_Rol),
    FOREIGN KEY (Id_Usuario) REFERENCES Usuario (Id_Usuario),
    FOREIGN KEY (Id_Rol)     REFERENCES Rol_Sistema (Id_Rol)
);

-- ---------------- MÓDULO 5: PROYECTOS CIENTÍFICOS -----------------------

CREATE TABLE Proyecto_Cientifico (
    Id_Proyecto     INT          NOT NULL,
    Nombre_Proyecto VARCHAR(120) NOT NULL,
    Fecha_Inicio    DATE         NOT NULL,
    Fecha_Termino   DATE         NULL,          -- NULL mientras el proyecto está en curso
    Estado          VARCHAR(15)  NOT NULL,
    PRIMARY KEY (Id_Proyecto),
    UNIQUE (Nombre_Proyecto),
    CHECK (Estado IN ('En curso', 'Finalizado', 'Suspendido')),
    CHECK (Fecha_Termino IS NULL OR Fecha_Termino >= Fecha_Inicio)
);

-- ESTUDIA: investigadores que participan en cada proyecto (N:M).
CREATE TABLE Estudia (
    Id_Proyecto INT         NOT NULL,
    Run         VARCHAR(12) NOT NULL,
    PRIMARY KEY (Id_Proyecto, Run),
    FOREIGN KEY (Id_Proyecto) REFERENCES Proyecto_Cientifico (Id_Proyecto),
    FOREIGN KEY (Run)         REFERENCES Investigacion (Run)
);

-- INVESTIGA: especies estudiadas por cada proyecto (N:M).
CREATE TABLE Investiga (
    Id_Proyecto INT NOT NULL,
    Id_Especie  INT NOT NULL,
    PRIMARY KEY (Id_Proyecto, Id_Especie),
    FOREIGN KEY (Id_Proyecto) REFERENCES Proyecto_Cientifico (Id_Proyecto),
    FOREIGN KEY (Id_Especie)  REFERENCES Especie (Id_Especie)
);

-- ASIGNAR: áreas donde se desarrolla cada proyecto (N:M).
CREATE TABLE Asignar (
    Id_Proyecto         INT NOT NULL,
    Anio_de_Declaracion INT NOT NULL,
    Numero_Correlativo  INT NOT NULL,
    Numero_Interno      INT NOT NULL,
    PRIMARY KEY (Id_Proyecto, Anio_de_Declaracion, Numero_Correlativo, Numero_Interno),
    FOREIGN KEY (Id_Proyecto) REFERENCES Proyecto_Cientifico (Id_Proyecto),
    FOREIGN KEY (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno)
        REFERENCES Area (Anio_de_Declaracion, Numero_Correlativo, Numero_Interno)
);
