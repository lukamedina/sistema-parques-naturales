# Sistema Integral de Gestión de Parques Naturales (Grupo 8)

TDFI103 Bases de Datos, Fase 2. PMV en Python y Streamlit con MySQL 8, listo para levantar con Docker
**sin internet** el día de la presentación.

## Qué hay

| Carpeta o archivo | Qué es |
|---|---|
| `pmv_parques/` | El PMV completo: código, SQL, generador de datos, `Dockerfile` y `docker-compose.yml`. Su README explica todo el uso normal. |
| `pruebas/prueba_pmv.py` | Prueba automática del PMV (34 verificaciones). |
| `pruebas/laboratorio_entrevista.sql` | Pruebas para Workbench: el error de cada restricción y los requerimientos modificados. |
| `pmv_parques_imagenes.tar` | Las imágenes `mysql:8.0` y `pmv_parques_app:1.0` ya construidas. No está en el repositorio porque pesa 446 MB: se baja desde [Releases](https://github.com/lukamedina/sistema-parques-naturales/releases/tag/imagenes-v1.0) y se deja en esta misma carpeta, al lado de `pmv_parques/`. |

## Despliegue en vivo (Luka y Martin)

Martin maneja la terminal y Docker. Luka maneja el navegador, Workbench y las demos del PMV.
Todos los comandos se ejecutan **dentro de `pmv_parques/`**.

### El día antes, con internet

1. Si cambió algún `.py`, el `Dockerfile` o `requirements.txt`, volver a construir y guardar las imágenes,
   porque el código va **dentro** de la imagen:

   ```bash
   docker compose build
   docker save -o ../pmv_parques_imagenes.tar mysql:8.0 pmv_parques_app:1.0
   ```

   Si solo cambió el SQL no hace falta: MySQL lee `sql/script_integral.sql` desde la carpeta.
2. Copiar a un pendrive `pmv_parques/`, `pruebas/` y `pmv_parques_imagenes.tar` (o clonar este repositorio
   y bajar el `.tar` desde Releases).
3. Si en ese computador se levantó antes el proyecto desde otra carpeta (por ejemplo `ProyectoDB`),
   ir a esa carpeta y ejecutar `docker compose down`. Si no, los contenedores viejos tienen los mismos
   nombres y el arranque falla (ver la tabla de abajo).
4. Hacer el ensayo completo de la sección siguiente en el computador que se va a usar.

### En la sala, sin internet

1. Abrir Docker Desktop y esperar a que diga que está corriendo.
2. Cargar las imágenes (solo la primera vez en ese computador):

   ```bash
   docker load -i ../pmv_parques_imagenes.tar
   ```

   Tiene que decir `Loaded image: mysql:8.0` y `Loaded image: pmv_parques_app:1.0`.
3. Partir con la base limpia y sin descargar nada:

   ```bash
   docker compose down -v
   docker compose up -d --no-build --pull never
   ```

   `--no-build` = no construir la app; `--pull never` = no descargar imágenes. En la prueba tardó
   22 segundos hasta `Container parques_pmv Started`.
4. `docker ps` tiene que mostrar `parques_mysql` (healthy) y `parques_pmv` (Up).
5. Luka abre http://localhost:8501 en tres pestañas (admin, operador y analista) y Workbench en
   `localhost`, puerto `3307`, usuario `root`, contraseña `Parques2026`.

Para mostrar la prueba automática (crea registros de prueba, así que después hay que repetir el paso 3):

```bash
docker cp ../pruebas/prueba_pmv.py parques_pmv:/tmp/prueba_pmv.py
docker exec -w /app parques_pmv python /tmp/prueba_pmv.py
```

Termina con `RESULTADO: TODO OK`.

### Si algo falla

| Qué pasa | Lo que se ve | Qué hacer |
|---|---|---|
| No se hizo `docker load` | `Error response from daemon: No such image: pmv_parques_app:1.0` | Hacer el paso 2. Con `--pull never` el error sale al tiro, en vez de quedarse intentando descargar. |
| Quedaron contenedores de otra carpeta con el mismo nombre | `Conflict. The container name "/parques_mysql" is already in use by container ...` | En la otra carpeta, `docker compose down`. |
| El puerto 3307 o el 8501 ya está ocupado | `Bind for 0.0.0.0:3307 failed: port is already allocated` | Cerrar el otro programa o cambiar el puerto de la izquierda en `docker-compose.yml`. |
| Se usó `--build` sin internet | Docker intenta bajar `python:3.12-slim` o las librerías y se cae (no se probó sin red) | Usar el comando del paso 3. |
| Se cambió un `.py` y no se volvió a guardar el `.tar` | La app de la sala muestra el código viejo | Repetir el paso 1 del día antes. |

Las imágenes son para procesadores Intel o AMD. En un Mac con chip M1, M2 o M3, Docker las corre
emulando: no se probó y va más lento, así que es mejor presentar desde un notebook con Windows o Linux.

## Cuentas de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin2026!` | Administrador |
| `operador` | `Operador2026!` | Operador |
| `analista` | `Analista2026!` | Analista |

## Volver a generar los datos

```bash
docker compose run --rm generador
```

Reescribe `sql/2_datos.sql` y `sql/script_integral.sql`. Como la semilla (2026) y la versión de Faker
(40.54.0) están fijas, salen idénticos byte a byte. Para que MySQL los cargue: `docker compose down -v`
y el paso 3.
