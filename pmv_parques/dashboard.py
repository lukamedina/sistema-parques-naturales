"""
dashboard.py - Funcionalidad 4: panel de información.

Cada pregunta se responde con UNA consulta SQL que ya entrega los datos listos
(agrupados y ordenados). Python solo dibuja el gráfico con Plotly.
Estas consultas son propias del PMV: no usan las vistas ni los procedimientos del informe.

Pregunta 1 (Fase 1): ¿Qué áreas reciben más visitantes mediante excursiones en un período?
Pregunta 2 (Fase 1): ¿Cómo se distribuyen las especies inventariadas entre vegetales, animales y minerales?
Pregunta 3 (Fase 1): ¿Existe relación entre la cantidad de visitantes de una excursión y su evaluación promedio?
Pregunta 4 (propuesta por el equipo): ¿En qué meses del año hay más visitantes?
    Justificación: la demanda no es pareja durante el año. Saber qué meses tienen más
    visitantes permite decidir cuántos guías y cupos programar cada mes, y dejar la
    mantención de senderos y áreas para los meses de menor demanda.

Criterio: "visitante" = inscripción con Asistencia = 'Asiste'.
"""
from datetime import date

import plotly.express as px
import streamlit as st

from db import consultar

# Uniones que se repiten en varias consultas (excursión -> área -> parque)
UNION_EXCURSION_AREA_PARQUE = """
    JOIN Area a           ON a.Anio_de_Declaracion = x.Anio_de_Declaracion
                         AND a.Numero_Correlativo  = x.Numero_Correlativo
                         AND a.Numero_Interno      = x.Numero_Interno
    JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                         AND p.Numero_Correlativo  = a.Numero_Correlativo
"""


def pregunta_1(desde, hasta, parque):
    st.subheader("1. ¿Qué áreas reciben más visitantes mediante excursiones?")
    datos = consultar(f"""
        SELECT CONCAT(p.Nombre_Parque, ' / ', a.Nombre_de_Area) AS Area,
               COUNT(DISTINCT x.Registro_Codigo) AS Excursiones,
               COUNT(i.Id_Inscripcion) AS Visitantes
        FROM Excursiones x
        {UNION_EXCURSION_AREA_PARQUE}
        JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
        WHERE i.Asistencia = 'Asiste'
          AND x.Fecha_Excursiones BETWEEN :desde AND :hasta
          AND (:parque = 'Todos' OR p.Nombre_Parque = :parque)
        GROUP BY p.Nombre_Parque, a.Nombre_de_Area
        ORDER BY Visitantes DESC
        LIMIT 10
    """, {"desde": desde, "hasta": hasta, "parque": parque})

    if len(datos) == 0:
        st.info("No hay visitantes en el período seleccionado.")
        return
    grafico = px.bar(datos, x="Visitantes", y="Area", orientation="h", text="Visitantes",
                     hover_data=["Excursiones"], title="Top 10 áreas con más visitantes")
    grafico.update_layout(yaxis={"categoryorder": "total ascending"}, yaxis_title="")
    st.plotly_chart(grafico)


def pregunta_2(parque):
    st.subheader("2. ¿Cómo se distribuyen las especies inventariadas entre vegetales, animales y minerales?")

    # Filtro por área: solo tiene sentido si se eligió un parque
    area = "Todas"
    if parque != "Todos":
        areas = consultar("""
            SELECT a.Nombre_de_Area
            FROM Area a
            JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                                 AND p.Numero_Correlativo  = a.Numero_Correlativo
            WHERE p.Nombre_Parque = :parque
            ORDER BY a.Nombre_de_Area
        """, {"parque": parque})
        area = st.selectbox("Área", ["Todas"] + list(areas["Nombre_de_Area"]))

    datos = consultar("""
        SELECT IFNULL(e.Tipo_Especie, 'Sin clasificar') AS Tipo,
               COUNT(DISTINCT e.Id_Especie) AS Especies_Distintas,
               SUM(i.Cantidad_Inventariada) AS Cantidad_Inventariada
        FROM Inventario_Especie i
        JOIN Especie e        ON e.Id_Especie = i.Id_Especie
        JOIN Area a           ON a.Anio_de_Declaracion = i.Anio_de_Declaracion
                             AND a.Numero_Correlativo  = i.Numero_Correlativo
                             AND a.Numero_Interno      = i.Numero_Interno
        JOIN Parque_Natural p ON p.Anio_de_Declaracion = a.Anio_de_Declaracion
                             AND p.Numero_Correlativo  = a.Numero_Correlativo
        WHERE (:parque = 'Todos' OR p.Nombre_Parque = :parque)
          AND (:area = 'Todas' OR a.Nombre_de_Area = :area)
        GROUP BY e.Tipo_Especie
        ORDER BY Especies_Distintas DESC
    """, {"parque": parque, "area": area})

    columna1, columna2 = st.columns(2)
    torta = px.pie(datos, names="Tipo", values="Especies_Distintas", title="Especies distintas por tipo")
    columna1.plotly_chart(torta)
    columna2.write("Detalle:")
    columna2.dataframe(datos, hide_index=True)
    columna2.caption("Los minerales se cuentan como afloramientos, por eso su cantidad inventariada es menor.")


def pregunta_3(desde, hasta, parque):
    st.subheader("3. ¿Existe relación entre la cantidad de visitantes de una excursión y su evaluación promedio?")
    datos = consultar(f"""
        SELECT x.Registro_Codigo AS Excursion,
               x.Fecha_Excursiones AS Fecha,
               p.Nombre_Parque AS Parque,
               a.Nombre_de_Area AS Area,
               COUNT(i.Id_Inscripcion) AS Visitantes,
               COUNT(ev.Calificacion) AS Evaluaciones,
               ROUND(AVG(ev.Calificacion), 2) AS Evaluacion_Promedio
        FROM Excursiones x
        {UNION_EXCURSION_AREA_PARQUE}
        JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
        LEFT JOIN Evaluacion ev ON ev.Registro_Codigo = i.Registro_Codigo
                               AND ev.Id_Visitante    = i.Id_Visitante
        WHERE i.Asistencia = 'Asiste'
          AND x.Fecha_Excursiones BETWEEN :desde AND :hasta
          AND (:parque = 'Todos' OR p.Nombre_Parque = :parque)
        GROUP BY x.Registro_Codigo, x.Fecha_Excursiones, p.Nombre_Parque, a.Nombre_de_Area
        HAVING COUNT(ev.Calificacion) > 0
        ORDER BY Visitantes DESC
    """, {"desde": desde, "hasta": hasta, "parque": parque})

    if len(datos) < 3:
        st.info("Se necesitan al menos 3 excursiones evaluadas para analizar la relación.")
        return

    datos["Evaluacion_Promedio"] = datos["Evaluacion_Promedio"].astype(float)
    dispersion = px.scatter(datos, x="Visitantes", y="Evaluacion_Promedio", hover_data=["Excursion", "Parque", "Area"],
                            title="Cada punto es una excursión")
    dispersion.update_layout(yaxis_title="Evaluación promedio (1 a 7)", yaxis_range=[0.5, 7.5])
    st.plotly_chart(dispersion)

    # Coeficiente de correlación: cerca de 0 = no hay relación; negativo = a más visitantes, peor nota
    correlacion = datos["Visitantes"].corr(datos["Evaluacion_Promedio"])
    st.metric("Coeficiente de correlación", f"{correlacion:.2f}")
    if correlacion < -0.3:
        st.write("Hay una relación **negativa**: las excursiones con más visitantes tienden a ser peor evaluadas.")
    elif correlacion > 0.3:
        st.write("Hay una relación **positiva**: las excursiones con más visitantes tienden a ser mejor evaluadas.")
    else:
        st.write("La relación es **débil**: la cantidad de visitantes casi no influye en la evaluación.")

    st.write("Detalle por excursión:")
    st.dataframe(datos, hide_index=True)


def pregunta_4(desde, hasta, parque):
    st.subheader("4. ¿En qué meses del año hay más visitantes? (pregunta propuesta por el equipo)")
    st.caption("Sirve para decidir cuántos guías y cupos programar cada mes y en qué meses hacer mantención.")
    datos = consultar(f"""
        SELECT MONTH(x.Fecha_Excursiones) AS Mes,
               COUNT(DISTINCT x.Registro_Codigo) AS Excursiones,
               COUNT(i.Id_Inscripcion) AS Visitantes
        FROM Excursiones x
        {UNION_EXCURSION_AREA_PARQUE}
        JOIN Inscripcion i ON i.Registro_Codigo = x.Registro_Codigo
        WHERE i.Asistencia = 'Asiste'
          AND x.Fecha_Excursiones BETWEEN :desde AND :hasta
          AND (:parque = 'Todos' OR p.Nombre_Parque = :parque)
        GROUP BY MONTH(x.Fecha_Excursiones)
        ORDER BY Mes
    """, {"desde": desde, "hasta": hasta, "parque": parque})

    if len(datos) == 0:
        st.info("No hay visitantes en el período seleccionado.")
        return
    barras = px.bar(datos, x="Mes", y="Visitantes", text="Visitantes", hover_data=["Excursiones"],
                    title="Visitantes por mes (1 = enero, 12 = diciembre)")
    barras.update_layout(xaxis={"dtick": 1})
    st.plotly_chart(barras)


def mostrar():
    st.title("Panel de información")

    # Filtros generales
    parques = consultar("SELECT Nombre_Parque FROM Parque_Natural WHERE Activo = 'Si' ORDER BY Nombre_Parque")
    columna1, columna2, columna3 = st.columns(3)
    desde = columna1.date_input("Desde", value=date(2026, 1, 1), format="DD/MM/YYYY")
    hasta = columna2.date_input("Hasta", value=date.today(), format="DD/MM/YYYY")
    parque = columna3.selectbox("Parque", ["Todos"] + list(parques["Nombre_Parque"]))

    st.divider()
    pregunta_1(desde, hasta, parque)
    st.divider()
    pregunta_2(parque)
    st.divider()
    pregunta_3(desde, hasta, parque)
    st.divider()
    pregunta_4(desde, hasta, parque)
