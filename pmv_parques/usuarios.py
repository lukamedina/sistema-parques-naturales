"""
usuarios.py - Funcionalidad 3 (administración): cuentas de usuario y sus roles.

Solo el rol Administrador ve esta página (lo controla app.py con PAGINAS_POR_ROL).
Permite ver todas las cuentas con sus roles y cambiar el estado de una cuenta
(Activa, Inactiva o Suspendida). Una cuenta que no está 'Activa' no puede iniciar sesión.
"""
import streamlit as st

from db import consultar, ejecutar

ESTADOS = ["Activa", "Inactiva", "Suspendida"]


def lista_usuarios():
    # GROUP_CONCAT junta los roles de cada usuario en un solo texto
    return consultar("""
        SELECT u.Id_Usuario, u.Nombre_Usuario,
               CONCAT(p.Primer_Nombre, ' ', p.Apellido_Paterno) AS Nombre,
               p.Labores AS Cargo,
               u.Estado_de_Cuenta,
               GROUP_CONCAT(r.Nombre_de_Rol) AS Roles
        FROM Usuario u
        JOIN Personal p    ON p.Run = u.Run
        JOIN Asignacion a  ON a.Id_Usuario = u.Id_Usuario
        JOIN Rol_Sistema r ON r.Id_Rol = a.Id_Rol
        GROUP BY u.Id_Usuario, u.Nombre_Usuario, p.Primer_Nombre, p.Apellido_Paterno, p.Labores, u.Estado_de_Cuenta
        ORDER BY u.Id_Usuario
    """)


def mostrar():
    st.title("Usuarios y roles")

    st.write("Permisos de cada rol:")
    st.table({
        "Rol": ["Administrador", "Operador", "Analista"],
        "Puede usar": ["Todo: panel, inscripciones, parques, especies y usuarios",
                       "Panel de información e inscripciones",
                       "Panel de información y consulta de parques y especies (sin modificar)"],
    })

    usuarios = lista_usuarios()
    with st.form("estado_cuenta"):
        elegido = st.selectbox("Cuenta", usuarios["Id_Usuario"].astype(str) + " | " + usuarios["Nombre_Usuario"]
                               + " | " + usuarios["Estado_de_Cuenta"])
        nuevo_estado = st.selectbox("Nuevo estado", ESTADOS)
        guardar = st.form_submit_button("Cambiar estado")

    if guardar:
        id_usuario = int(elegido.split(" | ")[0])
        if id_usuario == st.session_state["id_usuario"] and nuevo_estado != "Activa":
            st.error("No puedes desactivar tu propia cuenta.")
        else:
            ejecutar("UPDATE Usuario SET Estado_de_Cuenta = :estado WHERE Id_Usuario = :id",
                     {"estado": nuevo_estado, "id": id_usuario})
            st.success(f"La cuenta {elegido.split(' | ')[1]} ahora está {nuevo_estado}.")

    st.subheader("Cuentas registradas")
    st.dataframe(lista_usuarios(), hide_index=True)
