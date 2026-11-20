-- =========================================================================
-- SCRIPT INTEGRAL: Sistema Integral de Gestión de Parques Naturales
-- TDFI103 Bases de Datos, Fase 2, Grupo 8
--
-- Orden del script:
--   1. Base de datos
--   2. Tablas
--   3. Restricciones (PK, FK, NOT NULL, UNIQUE y CHECK)
--   4. Datos
--   5. Vistas (Felipe: R2, R3 y R5. Javier: R6, R7 y R8)
--   6. Procedimientos (Felipe: R4, R9 y R10. Javier: R1, R11 y R12)
--
-- Se ejecuta completo en MySQL 8.0 y crea la base desde cero.
-- Solo usa tipos básicos: INT, DECIMAL, VARCHAR, DATE y TIME.
-- Sí o no se guarda como texto: 'Si' o 'No'.
-- =========================================================================

SET NAMES utf8mb4;   -- para que se guarden bien las tildes y la ñ

-- -------------------------------------------------------------------------
-- 1. BASE DE DATOS
-- -------------------------------------------------------------------------
DROP DATABASE IF EXISTS Sistema_Integral_Parques_Naturales;
CREATE DATABASE Sistema_Integral_Parques_Naturales;
USE Sistema_Integral_Parques_Naturales;

-- =========================================================================
-- 2 y 3. TABLAS CON SUS RESTRICCIONES
-- =========================================================================

-- ---------------- MÓDULO 1: COMUNIDADES, PARQUES Y ÁREAS -----------------

-- Tabla: guarda las comunidades autónomas.
CREATE TABLE Comunidad_Autonoma (
    Codigo                VARCHAR(10)  NOT NULL,
    Nombre_Comunidad      VARCHAR(100) NOT NULL,
    Region_Administrativa VARCHAR(100) NOT NULL,
    Organismo_Responsable VARCHAR(150) NOT NULL,
    PRIMARY KEY (Codigo),
    UNIQUE (Nombre_Comunidad)
);

-- Tabla: guarda los parques. Activo = 'No' es un parque desactivado.
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

-- Tabla: guarda qué comunidades comparten cada parque y en qué porcentaje.
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

-- Tabla: guarda las áreas de cada parque (entidad débil del parque).
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

-- Tabla: guarda las especies. Tipo_Especie dice si es Vegetal, Animal o Mineral.
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

-- Tabla: guarda los datos que solo tienen las especies vegetales.
CREATE TABLE Especie_Vegetal (
    Id_Especie             INT          NOT NULL,
    Antecedentes_Floracion VARCHAR(100) NOT NULL,
    PRIMARY KEY (Id_Especie),
    FOREIGN KEY (Id_Especie) REFERENCES Especie (Id_Especie)
);

-- Tabla: guarda los datos que solo tienen las especies animales.
CREATE TABLE Especie_Animal (
    Id_Especie   INT         NOT NULL,
    Alimentacion VARCHAR(20) NOT NULL,
    Periodo_Celo VARCHAR(20) NOT NULL,
    PRIMARY KEY (Id_Especie),
    CHECK (Alimentacion IN ('Herbivoro', 'Carnivoro', 'Omnivoro', 'Insectivoro', 'Carronero', 'Piscivoro')),
    CHECK (Periodo_Celo IN ('Verano', 'Otono', 'Invierno', 'Primavera', 'Anual')),
    FOREIGN KEY (Id_Especie) REFERENCES Especie (Id_Especie)
);

-- Tabla: guarda los datos que solo tienen los minerales.
CREATE TABLE Especie_Mineral (
    Id_Especie INT         NOT NULL,
    Roca       VARCHAR(50) NULL,
    Cristales  VARCHAR(50) NULL,
    PRIMARY KEY (Id_Especie),
    CHECK (Roca IS NOT NULL OR Cristales IS NOT NULL),   -- debe tener al menos uno de los dos
    FOREIGN KEY (Id_Especie) REFERENCES Especie (Id_Especie)
);

-- Tabla: guarda cuántos ejemplares de cada especie hay en cada área.
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

-- Tabla: guarda las excursiones de cada área.
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

-- Tabla: guarda los visitantes.
CREATE TABLE Visitantes (
    Id_Visitante       VARCHAR(10)  NOT NULL,
    Nombre_Visitante   VARCHAR(80)  NOT NULL,
    Correo_Electronico VARCHAR(100) NOT NULL,
    PRIMARY KEY (Id_Visitante),
    UNIQUE (Correo_Electronico)
);

-- Tabla: guarda qué visitante se inscribió en qué excursión y si asistió.
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

-- Tabla: guarda la nota que pone cada visitante a una excursión.
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

-- Tabla: guarda a las personas que trabajan en los parques.
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

-- Tabla: guarda los teléfonos de cada persona.
CREATE TABLE Contacto (
    Run      VARCHAR(12) NOT NULL,
    Contacto VARCHAR(30) NOT NULL,
    PRIMARY KEY (Run, Contacto),
    FOREIGN KEY (Run) REFERENCES Personal (Run)
);

-- Tabla: guarda los trabajadores y quién los supervisa.
CREATE TABLE Trabajadores (
    Run            VARCHAR(12) NOT NULL,
    Run_Supervisor VARCHAR(12) NULL,
    PRIMARY KEY (Run),
    CHECK (Run_Supervisor IS NULL OR Run_Supervisor <> Run),   -- nadie se supervisa a sí mismo
    FOREIGN KEY (Run)            REFERENCES Personal (Run),
    FOREIGN KEY (Run_Supervisor) REFERENCES Trabajadores (Run)
);

-- Tabla: guarda qué personas son investigadores.
CREATE TABLE Investigacion (
    Run VARCHAR(12) NOT NULL,
    PRIMARY KEY (Run),
    FOREIGN KEY (Run) REFERENCES Personal (Run)
);

-- Tabla: guarda las funciones: Gestión, Vigilancia, Conservación e Investigación.
CREATE TABLE Funcion (
    Id_Funcion     INT         NOT NULL,
    Nombre_Funcion VARCHAR(40) NOT NULL,
    PRIMARY KEY (Id_Funcion),
    UNIQUE (Nombre_Funcion)
);

-- Tabla: guarda qué función cumple cada trabajador y en qué área.
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

-- Tabla: guarda los roles del PMV: Administrador, Operador y Analista.
CREATE TABLE Rol_Sistema (
    Id_Rol        INT         NOT NULL,
    Nombre_de_Rol VARCHAR(40) NOT NULL,
    PRIMARY KEY (Id_Rol),
    UNIQUE (Nombre_de_Rol)
);

-- Tabla: guarda las cuentas del PMV. La contraseña se guarda con SHA2.
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

-- Tabla: guarda qué rol tiene cada usuario.
CREATE TABLE Asignacion (
    Id_Usuario INT NOT NULL,
    Id_Rol     INT NOT NULL,
    PRIMARY KEY (Id_Usuario, Id_Rol),
    FOREIGN KEY (Id_Usuario) REFERENCES Usuario (Id_Usuario),
    FOREIGN KEY (Id_Rol)     REFERENCES Rol_Sistema (Id_Rol)
);

-- ---------------- MÓDULO 5: PROYECTOS CIENTÍFICOS -----------------------

-- Tabla: guarda los proyectos de investigación.
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

-- Tabla: guarda qué investigadores participan en cada proyecto.
CREATE TABLE Estudia (
    Id_Proyecto INT         NOT NULL,
    Run         VARCHAR(12) NOT NULL,
    PRIMARY KEY (Id_Proyecto, Run),
    FOREIGN KEY (Id_Proyecto) REFERENCES Proyecto_Cientifico (Id_Proyecto),
    FOREIGN KEY (Run)         REFERENCES Investigacion (Run)
);

-- Tabla: guarda qué especies estudia cada proyecto.
CREATE TABLE Investiga (
    Id_Proyecto INT NOT NULL,
    Id_Especie  INT NOT NULL,
    PRIMARY KEY (Id_Proyecto, Id_Especie),
    FOREIGN KEY (Id_Proyecto) REFERENCES Proyecto_Cientifico (Id_Proyecto),
    FOREIGN KEY (Id_Especie)  REFERENCES Especie (Id_Especie)
);

-- Tabla: guarda en qué áreas se hace cada proyecto.
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
