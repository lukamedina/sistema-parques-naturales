"""
inscripciones.py - Funcionalidad 1: formulario transaccional.

Pestaña 1 "Nueva inscripción": inscribe a un visitante en una excursión programada.
  Validaciones (todas con consultas SQL):
    - que se haya elegido un visitante;
    - que la excursión tenga cupos (inscritos < capacidad);
    - que el visitante no esté ya inscrito en esa excursión.
  La inscripción queda con Asistencia = 'Pendiente'.

Pestaña 2 "Registrar asistencia": en excursiones que ya ocurrieron, marca a cada
  inscrito como 'Asiste' o 'No Asiste'.
"""
import streamlit as st

from db import consultar, ejecutar


def nueva_inscripcion():
    # Excursiones de hoy en adelante, en áreas operativas de parques activos.
    # La misma consulta calcula los cupos libres y arma el texto que se muestra en la lista.
    excursiones = consultar("""
        SELECT x.Registro_Codigo,
               CONCAT(x.Registro_Codigo, ' | ', DATE_FORMAT(x.Fecha_Excursiones, '%d/%m/%Y'), ' ',
                      TIME_FORMAT(x.Horario_Excursiones, '%H:%i'), ' | ', p.Nombre_Parque, ' - ',
                      a.Nombre_de_Area, ' | ', x.Modalidad) AS Excursion,
               x.Capacidad,
               (SELECT COUNT(*) FROM Inscripcion i WHERE i.Registro_Codigo = x.Registro_Codigo) AS Inscritos
        FROM Excursiones x
        JOIN Area a           ON a.Anio_de_Declaracion = x.Anio_de_Declaracion
                             AND a.Numero_Correlativo  = x.Numero_Correlativo
                             AND a.Numero_Interno      = x.Numero_Interno
        JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                             AND p.Numero_Correlativo  = a.Numero_Correlativo
        WHERE x.Fecha_Excursiones >= CURDATE()
          AND a.Estado_Operativo = 'Operativa'
          AND p.Activo = 'Si'
        ORDER BY x.Fecha_Excursiones
    """)
    if len(excursiones) == 0:
        st.info("No hay excursiones programadas desde hoy en adelante.")
        return

    st.write("Excursiones programadas:")
    st.dataframe(excursiones[["Excursion", "Capacidad", "Inscritos"]], hide_index=True)

    visitantes = consultar("""
        SELECT CONCAT(Id_Visitante, ' | ', Nombre_Visitante) AS Visitante
        FROM Visitantes
        ORDER BY Nombre_Visitante
    """)

    with st.form("form_inscripcion", clear_on_submit=True):
        excursion = st.selectbox("Excursión", excursiones["Excursion"])
        visitante = st.selectbox("Visitante", visitantes["Visitante"], index=None,
                                 placeholder="Escribe un nombre para buscar")
        observaciones = st.text_input("Observaciones (opcional)", max_chars=100)
        enviar = st.form_submit_button("Inscribir visitante")

    if not enviar:
        return

    # Validación 1: debe elegir un visitante
    if visitante is None:
        st.error("Debes seleccionar un visitante.")
        return

    codigo = excursion.split(" | ")[0]        # "EX-161 | 05/12/2026 ..." -> "EX-161"
    id_visitante = visitante.split(" | ")[0]  # "V-0001 | Ana Soto"     -> "V-0001"

    # Validación 2: cupos disponibles
    cupos = consultar("""
        SELECT x.Capacidad,
               (SELECT COUNT(*) FROM Inscripcion i WHERE i.Registro_Codigo = x.Registro_Codigo) AS Inscritos
        FROM Excursiones x
        WHERE x.Registro_Codigo = :codigo
    """, {"codigo": codigo})
    if cupos["Inscritos"][0] >= cupos["Capacidad"][0]:
        st.error(f"La excursión {codigo} no tiene cupos disponibles.")
        return

    # Validación 3: el visitante no puede estar inscrito dos veces
    repetido = consultar("""
        SELECT COUNT(*) AS Cantidad
        FROM Inscripcion
        WHERE Registro_Codigo = :codigo AND Id_Visitante = :visitante
    """, {"codigo": codigo, "visitante": id_visitante})
    if repetido["Cantidad"][0] > 0:
        st.error("Ese visitante ya está inscrito en esta excursión.")
        return

    if observaciones.strip() == "":
        observaciones = None

    ejecutar("""
        INSERT INTO Inscripcion (Registro_Codigo, Id_Visitante, Fecha_Inscripcion, Asistencia, Observaciones)
        VALUES (:codigo, :visitante, CURDATE(), 'Pendiente', :observaciones)
    """, {"codigo": codigo, "visitante": id_visitante, "observaciones": observaciones})
    st.success(f"Inscripción registrada: {visitante} en la excursión {codigo}.")


def registrar_asistencia():
    # Inscripciones con asistencia pendiente de excursiones que ya ocurrieron
    pendientes = consultar("""
        SELECT CONCAT(i.Id_Inscripcion, ' | ', x.Registro_Codigo, ' | ',
                      DATE_FORMAT(x.Fecha_Excursiones, '%d/%m/%Y'), ' | ', v.Nombre_Visitante) AS Inscripcion
        FROM Inscripcion i
        JOIN Excursiones x ON x.Registro_Codigo = i.Registro_Codigo
        JOIN Visitantes v  ON v.Id_Visitante = i.Id_Visitante
        WHERE i.Asistencia = 'Pendiente'
          AND x.Fecha_Excursiones <= CURDATE()
        ORDER BY x.Fecha_Excursiones, v.Nombre_Visitante
    """)
    if len(pendientes) == 0:
        st.info("No hay inscripciones con asistencia pendiente en excursiones ya realizadas.")
        return

    st.write(f"Hay {len(pendientes)} inscripciones con asistencia pendiente.")
    with st.form("form_asistencia"):
        inscripcion = st.selectbox("Inscripción", pendientes["Inscripcion"])
        asistencia = st.radio("Asistencia", ["Asiste", "No Asiste"], horizontal=True)
        guardar = st.form_submit_button("Guardar asistencia")

    if guardar:
        id_inscripcion = int(inscripcion.split(" | ")[0])
        ejecutar("UPDATE Inscripcion SET Asistencia = :asistencia WHERE Id_Inscripcion = :id",
                 {"asistencia": asistencia, "id": id_inscripcion})
        st.success(f"Asistencia guardada: {inscripcion} -> {asistencia}.")


def mostrar():
    st.title("Inscripciones a excursiones")
    pestana1, pestana2 = st.tabs(["Nueva inscripción", "Registrar asistencia"])
    with pestana1:
        nueva_inscripcion()
    with pestana2:
        registrar_asistencia()
