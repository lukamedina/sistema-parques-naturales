"""
db.py - Conexión a la base de datos MySQL (SQLAlchemy + PyMySQL).

Solo tiene dos funciones, y todo el PMV las usa:
  consultar(sql, parametros) -> para SELECT. Devuelve una tabla (DataFrame de Pandas).
  ejecutar(sql, parametros)  -> para INSERT, UPDATE o DELETE. Guarda los cambios (COMMIT).

Los parámetros se escriben en el SQL como :nombre y se entregan en un diccionario.
Así nunca se pega texto del usuario directamente dentro del SQL (evita inyección SQL).
Ejemplo:
    consultar("SELECT * FROM Visitantes WHERE Id_Visitante = :id", {"id": "V-0001"})
"""
import os

import pandas as pd
from sqlalchemy import create_engine, text

# Datos de conexión. En Docker los entrega docker-compose.yml;
# si no existen, se usan los valores por defecto (MySQL instalado en el mismo computador).
USUARIO = os.getenv("DB_USER", "root")
CLAVE = os.getenv("DB_PASSWORD", "")
SERVIDOR = os.getenv("DB_HOST", "localhost")
PUERTO = os.getenv("DB_PORT", "3306")
BASE_DE_DATOS = os.getenv("DB_NAME", "Sistema_Integral_Parques_Naturales")

motor = create_engine(
    f"mysql+pymysql://{USUARIO}:{CLAVE}@{SERVIDOR}:{PUERTO}/{BASE_DE_DATOS}?charset=utf8mb4",
    pool_pre_ping=True,   # revisa que la conexión siga viva antes de usarla
)


def consultar(sql, parametros=None):
    """Ejecuta un SELECT y devuelve el resultado como tabla (DataFrame)."""
    with motor.connect() as conexion:
        return pd.read_sql(text(sql), conexion, params=parametros)


def ejecutar(sql, parametros=None):
    """Ejecuta un INSERT, UPDATE o DELETE y confirma los cambios (COMMIT)."""
    with motor.begin() as conexion:
        conexion.execute(text(sql), parametros or {})
