# Sistema Integral de Gestión de Parques Naturales (Grupo 8)

TDFI103 Bases de Datos, Fase 2. PMV en Python y Streamlit con MySQL 8, que se levanta con Docker.

## Qué hay

| Carpeta o archivo | Qué es |
|---|---|
| `pmv_parques/` | El PMV completo: código, `Dockerfile`, `docker-compose.yml`, SQL y generador de datos. Su README explica cada comando. |
| `pmv_parques/sql/script_integral.sql` | Un solo archivo que crea la base, las tablas, las restricciones, los datos, las 6 vistas y los 6 procedimientos. |
| `pmv_parques/generador/generar_datos.py` | Genera los datos con Faker y arma el script integral. |
| `pmv_parques/sql/verificar.sql` | Muestra cuántos datos y objetos tiene la base. |
| `pruebas/prueba_pmv.py` | Prueba automática del PMV (34 verificaciones). |
| `pruebas/laboratorio_entrevista.sql` | Pruebas para Workbench: el error de cada restricción y los requerimientos modificados. |

## Despliegue en vivo (Luka y Martin)

GitHub es el pendrive: el proyecto se baja con git en el computador de la presentación.
Martin maneja la terminal; Luka maneja el navegador, Workbench y las demos.

### El día antes, con internet, en el computador que se va a usar

```bash
git clone https://github.com/lukamedina/sistema-parques-naturales.git
cd sistema-parques-naturales/pmv_parques
docker compose up --build -d
```

Esto descarga MySQL 8.0.46 y Python 3.12.13 (versiones fijas, iguales en Windows, macOS y Linux),
construye la app y crea la base. En la prueba tardó 93 segundos la primera vez. Después, hacer el ensayo
completo de la sección siguiente.

- Si ese computador ya tenía contenedores `parques_mysql` o `parques_pmv` levantados desde otra carpeta
  (por ejemplo `ProyectoDB`), ejecutar antes `docker compose down` en esa carpeta.
- Si después se sube algún cambio a GitHub: `git pull` y otra vez `docker compose up --build -d`.
- En Windows, Docker Desktop necesita WSL2 y la virtualización activada. Por eso el ensayo se hace en
  ese mismo computador.

### En la sala: lo que se muestra

Todo dentro de `pmv_parques`:

| Acción | Comando | Qué se ve |
|---|---|---|
| Levantar | `docker compose up --build -d` | Construye la app con el `Dockerfile` y MySQL ejecuta el script integral. Termina con `Container parques_pmv Started`. |
| Ver los datos | `docker compose exec db mysql -uroot -pParques2026 -t -e "source /verificar.sql"` | Filas por tabla (por ejemplo, 1342 inscripciones) y 26 tablas, 6 vistas y 6 procedimientos. |
| Borrar | `docker compose down -v` | `Volume pmv_parques_datos_mysql Removed`: la base ya no existe. |
| Volver a crear | `docker compose up -d` | El script corre de nuevo y la base queda como recién creada, en unos 20 segundos. |
| Crear los datos | `docker compose run --rm generador` | Faker vuelve a escribir `sql/2_datos.sql` y `sql/script_integral.sql`, idénticos byte a byte. |

Si en la sala no hay internet, levantar con `docker compose up -d`, sin `--build`: usa lo que se
descargó el día antes y no construye ni descarga nada.

Luka abre http://localhost:8501 en tres pestañas (admin, operador y analista) y Workbench en
`localhost`, puerto `3307`, usuario `root`, contraseña `Parques2026`.

Prueba automática (crea registros de prueba; después, `docker compose down -v` y `docker compose up -d`):

```bash
docker cp ../pruebas/prueba_pmv.py parques_pmv:/tmp/prueba_pmv.py
docker exec -w /app parques_pmv python /tmp/prueba_pmv.py
```

Termina con `RESULTADO: TODO OK`.

### Si algo falla

| Qué pasa | Lo que se ve | Qué hacer |
|---|---|---|
| Quedaron contenedores de otra carpeta con el mismo nombre | `Conflict. The container name "/parques_mysql" is already in use by container ...` | En la otra carpeta, `docker compose down`. |
| El puerto 3307 o el 8501 ya está ocupado | `Bind for 0.0.0.0:3307 failed: port is already allocated` | Cerrar el otro programa o cambiar el puerto de la izquierda en `docker-compose.yml`. |
| Se cambió un `.py` y se levantó sin `--build` | La app sigue con el código anterior | `docker compose up --build -d`. |

## Cuentas de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin2026!` | Administrador |
| `operador` | `Operador2026!` | Operador |
| `analista` | `Analista2026!` | Analista |
