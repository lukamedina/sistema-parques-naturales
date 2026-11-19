# PMV: Sistema Integral de Gestión de Parques Naturales (Grupo 8)

Aplicación web en Python y Streamlit conectada a MySQL 8. Tiene las cuatro funcionalidades
que pide la Fase 2: formulario transaccional, CRUD, control de usuarios y panel de información.

## Ejecutar con Docker

Requisito: tener Docker Desktop instalado y abierto. Todos los comandos van en una terminal
abierta en esta carpeta (la que tiene `docker-compose.yml`). Son los mismos en Windows, macOS y Linux.

### 1. Levantar todo

```bash
docker compose up --build -d
```

- `--build` construye la imagen de la aplicación con el `Dockerfile`.
- El servicio `db` (MySQL 8.0.46) ejecuta `sql/script_integral.sql`: crea la base, las 26 tablas con sus
  restricciones, los datos, las 6 vistas y los 6 procedimientos.
- La aplicación parte sola cuando MySQL termina de cargar. La primera vez tarda un par de minutos
  porque descarga MySQL y Python; después, unos 20 segundos.

Abrir en el navegador: **http://localhost:8501**

### 2. Ver que los datos se crearon

```bash
docker compose ps
docker compose exec db mysql -uroot -pParques2026 -t -e "source /verificar.sql"
```

El segundo comando ejecuta `sql/verificar.sql` dentro de MySQL y muestra cuántas filas tiene cada tabla
y cuántas tablas, vistas y procedimientos hay (26, 6 y 6). La advertencia `Using a password on the
command line` es normal.

### 3. Borrar todo y volver a crearlo

```bash
docker compose down -v
docker compose up -d
```

`down -v` borra los contenedores y el volumen `datos_mysql`, donde vive la base. El siguiente `up`
encuentra el volumen vacío y vuelve a ejecutar el script completo, así que la base queda como recién
creada (se pierde todo lo que se haya cambiado desde la aplicación).

Para solo detener, sin borrar los datos: `docker compose down`.

La base también se puede abrir desde MySQL Workbench: host `localhost`, puerto **3307**,
usuario `root`, contraseña `Parques2026`.

## Generar los datos (script de poblamiento)

Los datos ya vienen generados dentro de `sql/script_integral.sql`, así que este paso solo es
necesario si se cambia el generador. El script `generador/generar_datos.py` usa Faker para
crear `sql/2_datos.sql` y después arma el script integral juntando:

```text
sql/1_estructura.sql  +  sql/2_datos.sql  +  sql/3_vistas_procedimientos.sql  =  sql/script_integral.sql
```

Con Docker (no hay que instalar Python ni Faker en el computador):

```bash
docker compose run --rm generador
```

Sin Docker (Python 3.12+): `pip install -r requirements.txt` y luego
`python generador/generar_datos.py`.

La semilla es fija (`SEMILLA = 2026`) y la versión de Faker también, así que siempre se generan
exactamente los mismos datos. Para que MySQL cargue el script nuevo hay que borrar y volver a crear
la base (`docker compose down -v` y `docker compose up -d`).

## Sin internet

La primera vez Docker descarga MySQL, Python y las librerías, y las deja guardadas en el computador.
Si después no hay internet, `docker compose up -d` (sin `--build`) funciona igual: usa lo que ya está
guardado y no descarga nada. Por eso conviene levantar el proyecto una vez, con internet, en el
computador que se va a usar.

## Cuentas de demostración

| Usuario    | Contraseña      | Rol           |
|------------|-----------------|---------------|
| `admin`    | `Admin2026!`    | Administrador |
| `operador` | `Operador2026!` | Operador      |
| `analista` | `Analista2026!` | Analista      |

Las otras 47 cuentas usan `Parques2026!`. Algunas están Inactivas o Suspendidas a propósito,
para mostrar que no pueden entrar.

## Permisos por rol

| Sección                                          | Administrador | Operador | Analista |
|--------------------------------------------------|:-------------:|:--------:|:--------:|
| Panel de información                             | Sí            | Sí       | Sí       |
| Inscripciones y asistencia                       | Sí            | Sí       | No       |
| Parques y especies: consultar                    | Sí            | No       | Sí       |
| Parques y especies: crear, modificar, desactivar | Sí            | No       | No       |
| Usuarios y roles                                 | Sí            | No       | No       |

## Archivos

| Archivo                          | Funcionalidad                                   | Responsable principal |
|----------------------------------|-------------------------------------------------|-----------------------|
| `inscripciones.py`               | 1. Formulario transaccional                     | (completar)           |
| `parques.py`, `especies.py`      | 2. CRUD de parques y especies                   | (completar)           |
| `app.py`, `usuarios.py`          | 3. Control de usuarios (login y menú por rol)   | (completar)           |
| `dashboard.py`                   | 4. Panel de información (4 preguntas)           | (completar)           |
| `db.py`                          | Conexión a MySQL: `consultar()` y `ejecutar()`  | (completar)           |
| `Dockerfile`, `docker-compose.yml` | Despliegue                                    | (completar)           |
| `sql/script_integral.sql`        | Base de datos completa                          | (completar)           |
| `generador/generar_datos.py`     | Poblamiento sintético con Faker                 | (completar)           |

## Fechas de los datos

Las inscripciones solo se permiten en excursiones de hoy en adelante, y la asistencia solo se
registra en excursiones que ya pasaron. Los datos traen 20 excursiones programadas entre
noviembre de 2026 y enero de 2027.

## Ejecutar sin Docker

Con MySQL 8 instalado y `sql/script_integral.sql` ya ejecutado en Workbench:

```bash
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
$env:DB_PASSWORD="tu_contraseña"
streamlit run app.py
```

macOS o Linux: `DB_PASSWORD=tu_contraseña streamlit run app.py`

Variables disponibles: `DB_HOST` (localhost), `DB_PORT` (3306), `DB_USER` (root),
`DB_PASSWORD` (vacía) y `DB_NAME` (Sistema_Integral_Parques_Naturales).
