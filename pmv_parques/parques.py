"""
parques.py - Funcionalidad 2: CRUD de la tabla Parque_Natural.

  Consultar : lista de parques (todos los roles con acceso).
  Crear     : INSERT de un parque nuevo.          (solo Administrador)
  Modificar : UPDATE de los datos de un parque.   (solo Administrador)
  Desactivar: UPDATE Activo = 'No'.               (solo Administrador)

¿Por qué desactivar y no borrar? Un parque tiene áreas, y esas áreas tienen
excursiones, inventarios y personal. Un DELETE violaría la integridad referencial
(las claves foráneas lo impiden), por eso se usa eliminación LÓGICA.
"""
import streamlit as st

from db import consultar, ejecutar

ESTADOS = ["Bueno", "Regular", "Critico"]


def lista_parques():
    return consultar("""
        SELECT CONCAT(p.Anio_de_Declaracion, '-', p.Numero_Correlativo) AS Rol,
               p.Nombre_Parque, p.Fecha_de_Declaracion, p.Superficie_Total, p.Presupuesto_Anual,
               p.Estado_de_Conservacion, p.Ubicacion, c.Nombre_Comunidad, p.Activo
        FROM Parque_Natural p
        JOIN Comunidad_Autonoma c ON c.Codigo = p.Codigo_Comunidad
        ORDER BY p.Nombre_Parque
    """)


def crear_parque():
    comunidades = consultar("SELECT CONCAT(Codigo, ' | ', Nombre_Comunidad) AS Comunidad FROM Comunidad_Autonoma")

    with st.form("crear_parque", clear_on_submit=True):
        nombre = st.text_input("Nombre del parque", max_chars=80)
        fecha = st.date_input("Fecha de declaración")
        superficie = st.number_input("Superficie total (hectáreas)", min_value=0.0, step=100.0)
        presupuesto = st.number_input("Presupuesto anual ($)", min_value=0, step=1000000)
        estado = st.selectbox("Estado de conservación", ESTADOS)
        ubicacion = st.text_input("Ubicación (región)", max_chars=80)
        comunidad = st.selectbox("Comunidad principal responsable", comunidades["Comunidad"])
        guardar = st.form_submit_button("Crear parque")

    if not guardar:
        return
    if nombre.strip() == "" or ubicacion.strip() == "":
        st.error("El nombre y la ubicación son obligatorios.")
        return
    if superficie <= 0 or presupuesto <= 0:
        st.error("La superficie y el presupuesto deben ser mayores que cero.")
        return
    repetido = consultar("SELECT COUNT(*) AS Cantidad FROM Parque_Natural WHERE Nombre_Parque = :nombre",
                         {"nombre": nombre.strip()})
    if repetido["Cantidad"][0] > 0:
        st.error("Ya existe un parque con ese nombre.")
        return

    # El rol del parque = año de declaración + siguiente correlativo de ese año
    anio = fecha.year
    siguiente = consultar("""
        SELECT IFNULL(MAX(Numero_Correlativo), 0) + 1 AS Correlativo
        FROM Parque_Natural
        WHERE Anio_de_Declaracion = :anio
    """, {"anio": anio})
    correlativo = int(siguiente["Correlativo"][0])
    codigo_comunidad = comunidad.split(" | ")[0]

    ejecutar("""
        INSERT INTO Parque_Natural (Anio_de_Declaracion, Numero_Correlativo, Nombre_Parque, Fecha_de_Declaracion,
                                    Superficie_Total, Presupuesto_Anual, Estado_de_Conservacion, Ubicacion,
                                    Activo, Codigo_Comunidad)
        VALUES (:anio, :correlativo, :nombre, :fecha, :superficie, :presupuesto, :estado, :ubicacion,
                'Si', :comunidad)
    """, {"anio": anio, "correlativo": correlativo, "nombre": nombre.strip(), "fecha": fecha,
          "superficie": superficie, "presupuesto": presupuesto, "estado": estado,
          "ubicacion": ubicacion.strip(), "comunidad": codigo_comunidad})

    # La comunidad principal participa con el 100% del territorio del parque nuevo
    ejecutar("""
        INSERT INTO Participacion_Comunidad (Codigo_Comunidad, Anio_de_Declaracion, Numero_Correlativo,
                                             Porcentaje_Territorial)
        VALUES (:comunidad, :anio, :correlativo, 100)
    """, {"comunidad": codigo_comunidad, "anio": anio, "correlativo": correlativo})
    st.success(f"Parque '{nombre.strip()}' creado con rol {anio}-{correlativo}.")


def modificar_parque(parques):
    rol = st.selectbox("Parque a modificar", parques["Rol"] + " | " + parques["Nombre_Parque"])
    anio = int(rol.split(" | ")[0].split("-")[0])
    correlativo = int(rol.split(" | ")[0].split("-")[1])

    actual = consultar("""
        SELECT * FROM Parque_Natural
        WHERE Anio_de_Declaracion = :anio AND Numero_Correlativo = :correlativo
    """, {"anio": anio, "correlativo": correlativo})

    with st.form("modificar_parque"):
        st.caption("El rol (año + correlativo) es la clave primaria y no se modifica.")
        nombre = st.text_input("Nombre del parque", value=actual["Nombre_Parque"][0], max_chars=80)
        superficie = st.number_input("Superficie total (hectáreas)", min_value=0.0,
                                     value=float(actual["Superficie_Total"][0]), step=100.0)
        presupuesto = st.number_input("Presupuesto anual ($)", min_value=0,
                                      value=int(actual["Presupuesto_Anual"][0]), step=1000000)
        estado = st.selectbox("Estado de conservación", ESTADOS,
                              index=ESTADOS.index(actual["Estado_de_Conservacion"][0]))
        ubicacion = st.text_input("Ubicación (región)", value=actual["Ubicacion"][0], max_chars=80)
        guardar = st.form_submit_button("Guardar cambios")

    if not guardar:
        return
    if nombre.strip() == "" or superficie <= 0 or presupuesto <= 0:
        st.error("El nombre es obligatorio y la superficie y el presupuesto deben ser mayores que cero.")
        return

    ejecutar("""
        UPDATE Parque_Natural
        SET Nombre_Parque = :nombre, Superficie_Total = :superficie, Presupuesto_Anual = :presupuesto,
            Estado_de_Conservacion = :estado, Ubicacion = :ubicacion
        WHERE Anio_de_Declaracion = :anio AND Numero_Correlativo = :correlativo
    """, {"nombre": nombre.strip(), "superficie": superficie, "presupuesto": presupuesto, "estado": estado,
          "ubicacion": ubicacion.strip(), "anio": anio, "correlativo": correlativo})
    st.success("Parque actualizado.")


def activar_desactivar_parque(parques):
    rol = st.selectbox("Parque", parques["Rol"] + " | " + parques["Nombre_Parque"] + " | Activo: " + parques["Activo"])
    anio = int(rol.split(" | ")[0].split("-")[0])
    correlativo = int(rol.split(" | ")[0].split("-")[1])

    columna1, columna2 = st.columns(2)
    if columna1.button("Desactivar parque"):
        ejecutar("""
            UPDATE Parque_Natural SET Activo = 'No'
            WHERE Anio_de_Declaracion = :anio AND Numero_Correlativo = :correlativo
        """, {"anio": anio, "correlativo": correlativo})
        st.success("Parque desactivado (eliminación lógica). Ya no aparece para nuevas inscripciones.")
    if columna2.button("Reactivar parque"):
        ejecutar("""
            UPDATE Parque_Natural SET Activo = 'Si'
            WHERE Anio_de_Declaracion = :anio AND Numero_Correlativo = :correlativo
        """, {"anio": anio, "correlativo": correlativo})
        st.success("Parque reactivado.")


def mostrar(puede_editar):
    st.title("Parques naturales")

    if puede_editar:
        accion = st.radio("¿Qué quieres hacer?", ["Crear", "Modificar", "Desactivar o reactivar"], horizontal=True)
        if accion == "Crear":
            crear_parque()
        elif accion == "Modificar":
            modificar_parque(lista_parques())
        else:
            activar_desactivar_parque(lista_parques())
        st.divider()
    else:
        st.info("Tu rol solo permite consultar. Para crear o modificar se necesita el rol Administrador.")

    # El listado va al final para que muestre los cambios recién guardados
    st.subheader("Listado de parques")
    st.dataframe(lista_parques(), hide_index=True)
