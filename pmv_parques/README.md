# PMV: Sistema Integral de Gestión de Parques Naturales (Grupo 8)

Aplicación web en Python y Streamlit conectada a MySQL 8. Tiene las cuatro funcionalidades
que pide la Fase 2: formulario transaccional, CRUD, control de usuarios y panel de información.

## Ejecutar con Docker

Requisito: tener Docker Desktop instalado y abierto.

1. Abrir una terminal en esta carpeta (la que tiene `docker-compose.yml`).
2. Ejecutar:

   ```bash
   docker compose up --build
   ```

   La primera vez crea la base de datos y ejecuta `sql/script_integral.sql` completo.
   La aplicación parte sola cuando MySQL termina de cargar.
3. Abrir en el navegador: **http://localhost:8501**

Para detenerla: `Ctrl + C` en la terminal, o `docker compose down`.

Para reiniciar la base de datos desde cero (borra los cambios hechos desde la aplicación):

```bash
docker compose down -v
docker compose up --build
```

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

La semilla es fija (`SEMILLA = 2026`), así que siempre se generan exactamente los mismos datos.
Para que MySQL cargue el script nuevo hay que reiniciar la base (`docker compose down -v` y
`docker compose up --build`).

## Ejecutar sin internet (respaldo para la presentación)

`docker compose up --build` descarga MySQL, Python y las librerías desde internet. Si en el
lugar de la presentación no hay red, se pueden llevar las imágenes ya construidas en un archivo:

1. En un computador **con internet**, dentro de esta carpeta:

   ```bash
   docker compose build
   docker save -o ../pmv_parques_imagenes.tar mysql:8.0 pmv_parques_app:1.0
   ```

   El archivo queda fuera de la carpeta del proyecto (pesa unos 450 MB; no se sube a Canvas).
2. En el computador de la presentación, copiar la carpeta del proyecto y el archivo `.tar`, y:

   ```bash
   docker load -i ../pmv_parques_imagenes.tar
   docker compose up
   ```

   Aquí va **sin** `--build`: las imágenes ya están cargadas y no se descarga nada.

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
