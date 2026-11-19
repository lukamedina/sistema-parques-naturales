"""
especies.py - Funcionalidad 2: CRUD de la tabla Especie (y sus subtipos).

  Consultar : lista de especies con su tipo.     (todos los roles con acceso)
  Crear     : INSERT en Especie y en la tabla del subtipo (Vegetal, Animal o Mineral).
  Modificar : UPDATE de los datos comunes de la especie.
  Desactivar: UPDATE Activo = 'No' (eliminación lógica, porque la especie puede
              estar en inventarios y proyectos: un DELETE violaría las claves foráneas).

Generalización DISJUNTA y PARCIAL: una especie es Vegetal, Animal, Mineral o
"Sin clasificar" (Tipo_Especie = NULL), y nunca dos tipos a la vez.
"""
import streamlit as st

from db import consultar, ejecutar

ESTADOS = ["Preocupacion Menor", "Casi Amenazada", "Vulnerable", "En Peligro", "Peligro Critico"]
TIPOS = ["Vegetal", "Animal", "Mineral", "Sin clasificar"]
ALIMENTACION = ["Herbivoro", "Carnivoro", "Omnivoro", "Insectivoro", "Carronero", "Piscivoro"]
CELO = ["Verano", "Otono", "Invierno", "Primavera", "Anual"]


def lista_especies():
    # LEFT JOIN con los subtipos: cada especie trae los datos de su subtipo (o NULL si no tiene)
    return consultar("""
        SELECT e.Id_Especie, e.Nombre_Vulgar, e.Denominacion_Cientifica,
               IFNULL(e.Tipo_Especie, 'Sin clasificar') AS Tipo, e.Estado_de_Conservacion,
               v.Antecedentes_Floracion, an.Alimentacion, an.Periodo_Celo, m.Roca, m.Cristales, e.Activo
        FROM Especie e
        LEFT JOIN Especie_Vegetal v  ON v.Id_Especie  = e.Id_Especie
        LEFT JOIN Especie_Animal an  ON an.Id_Especie = e.Id_Especie
        LEFT JOIN Especie_Mineral m  ON m.Id_Especie  = e.Id_Especie
        ORDER BY e.Nombre_Vulgar
    """)


def crear_especie():
    # El tipo se elige FUERA del formulario para que aparezcan los campos de ese subtipo
    tipo = st.radio("Tipo de especie", TIPOS, horizontal=True)

    with st.form("crear_especie", clear_on_submit=True):
        cientifico = st.text_input("Denominación científica", max_chars=150)
        vulgar = st.text_input("Nombre vulgar (común)", max_chars=80)
        estado = st.selectbox("Estado de conservación", ESTADOS)
        floracion = alimentacion = celo = roca = cristales = ""
        if tipo == "Vegetal":
            floracion = st.text_input("Antecedentes de floración", max_chars=100)
        elif tipo == "Animal":
            alimentacion = st.selectbox("Alimentación", ALIMENTACION)
            celo = st.selectbox("Período de celo", CELO)
        elif tipo == "Mineral":
            roca = st.text_input("Roca", max_chars=50)
            cristales = st.text_input("Cristales", max_chars=50)
        else:
            st.caption("Las especies sin clasificar (hongos, líquenes, algas) no tienen datos de subtipo.")
        guardar = st.form_submit_button("Crear especie")

    if not guardar:
        return
    # Validaciones
    if cientifico.strip() == "" or vulgar.strip() == "":
        st.error("La denominación científica y el nombre vulgar son obligatorios.")
        return
    if tipo == "Vegetal" and floracion.strip() == "":
        st.error("Para una especie vegetal debes indicar los antecedentes de floración.")
        return
    if tipo == "Mineral" and roca.strip() == "" and cristales.strip() == "":
        st.error("Para un mineral debes indicar la roca o los cristales.")
        return
    repetida = consultar("SELECT COUNT(*) AS Cantidad FROM Especie WHERE Denominacion_Cientifica = :c",
                         {"c": cientifico.strip()})
    if repetida["Cantidad"][0] > 0:
        st.error("Ya existe una especie con esa denominación científica.")
        return

    tipo_bd = tipo
    if tipo == "Sin clasificar":
        tipo_bd = None          # en la base de datos, sin clasificar = NULL

    # 1) Insertar en la tabla general (Id_Especie es AUTO_INCREMENT)
    ejecutar("""
        INSERT INTO Especie (Denominacion_Cientifica, Nombre_Vulgar, Estado_de_Conservacion,
                             Fecha_Especie, Tipo_Especie, Activo)
        VALUES (:cientifico, :vulgar, :estado, CURDATE(), :tipo, 'Si')
    """, {"cientifico": cientifico.strip(), "vulgar": vulgar.strip(), "estado": estado, "tipo": tipo_bd})

    # 2) Buscar el Id que MySQL le asignó (la denominación científica es UNIQUE)
    nueva = consultar("SELECT Id_Especie FROM Especie WHERE Denominacion_Cientifica = :c",
                      {"c": cientifico.strip()})
    id_especie = int(nueva["Id_Especie"][0])

    # 3) Insertar en la tabla del subtipo
    if tipo == "Vegetal":
        ejecutar("INSERT INTO Especie_Vegetal (Id_Especie, Antecedentes_Floracion) VALUES (:id, :f)",
                 {"id": id_especie, "f": floracion.strip()})
    elif tipo == "Animal":
        ejecutar("INSERT INTO Especie_Animal (Id_Especie, Alimentacion, Periodo_Celo) VALUES (:id, :a, :c)",
                 {"id": id_especie, "a": alimentacion, "c": celo})
    elif tipo == "Mineral":
        ejecutar("INSERT INTO Especie_Mineral (Id_Especie, Roca, Cristales) VALUES (:id, :r, :c)",
                 {"id": id_especie, "r": roca.strip() or None, "c": cristales.strip() or None})

    st.success(f"Especie '{vulgar.strip()}' creada con Id {id_especie} ({tipo}).")


def modificar_especie(especies):
    elegida = st.selectbox("Especie a modificar",
                           especies["Id_Especie"].astype(str) + " | " + especies["Nombre_Vulgar"])
    id_especie = int(elegida.split(" | ")[0])

    actual = consultar("SELECT * FROM Especie WHERE Id_Especie = :id", {"id": id_especie})

    with st.form("modificar_especie"):
        st.caption("El tipo no se cambia (la especialización es disjunta).")
        cientifico = st.text_input("Denominación científica", value=actual["Denominacion_Cientifica"][0],
                                   max_chars=150)
        vulgar = st.text_input("Nombre vulgar (común)", value=actual["Nombre_Vulgar"][0], max_chars=80)
        estado = st.selectbox("Estado de conservación", ESTADOS,
                              index=ESTADOS.index(actual["Estado_de_Conservacion"][0]))
        guardar = st.form_submit_button("Guardar cambios")

    if not guardar:
        return
    if cientifico.strip() == "" or vulgar.strip() == "":
        st.error("La denominación científica y el nombre vulgar son obligatorios.")
        return

    ejecutar("""
        UPDATE Especie
        SET Denominacion_Cientifica = :cientifico, Nombre_Vulgar = :vulgar, Estado_de_Conservacion = :estado
        WHERE Id_Especie = :id
    """, {"cientifico": cientifico.strip(), "vulgar": vulgar.strip(), "estado": estado, "id": id_especie})
    st.success("Especie actualizada.")


def activar_desactivar_especie(especies):
    elegida = st.selectbox("Especie", especies["Id_Especie"].astype(str) + " | " + especies["Nombre_Vulgar"]
                           + " | Activo: " + especies["Activo"])
    id_especie = int(elegida.split(" | ")[0])

    columna1, columna2 = st.columns(2)
    if columna1.button("Desactivar especie"):
        ejecutar("UPDATE Especie SET Activo = 'No' WHERE Id_Especie = :id", {"id": id_especie})
        st.success("Especie desactivada (eliminación lógica).")
    if columna2.button("Reactivar especie"):
        ejecutar("UPDATE Especie SET Activo = 'Si' WHERE Id_Especie = :id", {"id": id_especie})
        st.success("Especie reactivada.")


def mostrar(puede_editar):
    st.title("Especies")

    if puede_editar:
        accion = st.radio("¿Qué quieres hacer?", ["Crear", "Modificar", "Desactivar o reactivar"], horizontal=True)
        if accion == "Crear":
            crear_especie()
        elif accion == "Modificar":
            modificar_especie(lista_especies())
        else:
            activar_desactivar_especie(lista_especies())
        st.divider()
    else:
        st.info("Tu rol solo permite consultar. Para crear o modificar se necesita el rol Administrador.")

    # El listado va al final para que muestre los cambios recién guardados
    st.subheader("Listado de especies")
    st.dataframe(lista_especies(), hide_index=True)
