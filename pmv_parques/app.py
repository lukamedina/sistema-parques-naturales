"""
app.py - PMV: Sistema Integral de Gestión de Parques Naturales (Grupo 8).

Es el archivo principal. Hace dos cosas:
  1. Funcionalidad 3 (control de usuarios): inicio de sesión y menú según el rol.
  2. Llama a la página que el usuario elige en el menú:
       - dashboard.py      -> Funcionalidad 4: panel de información
       - inscripciones.py  -> Funcionalidad 1: formulario transaccional
       - parques.py        -> Funcionalidad 2: CRUD de Parques
       - especies.py       -> Funcionalidad 2: CRUD de Especies
       - usuarios.py       -> administración de cuentas (solo Administrador)

Para ejecutar:  streamlit run app.py
"""
import streamlit as st

import dashboard
import especies
import inscripciones
import parques
import usuarios
from db import consultar

st.set_page_config(page_title="Parques Naturales", page_icon="🌲", layout="wide")

# Páginas que puede ver cada rol (esto es lo que controla los permisos).
PAGINAS_POR_ROL = {
    "Administrador": ["Panel de información", "Inscripciones", "Parques", "Especies", "Usuarios"],
    "Operador": ["Panel de información", "Inscripciones"],
    "Analista": ["Panel de información", "Parques", "Especies"],
}


def pantalla_login():
    st.title("🌲 Parques Naturales")
    st.write("Ingresa con tu cuenta de usuario.")

    with st.form("login"):
        nombre_usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Ingresar")

    if entrar:
        # La contraseña se compara encriptada: SHA2 hace lo mismo que se hizo al guardarla.
        cuenta = consultar("""
            SELECT u.Id_Usuario, u.Nombre_Usuario,
                   CONCAT(p.Primer_Nombre, ' ', p.Apellido_Paterno) AS Nombre
            FROM Usuario u
            JOIN Personal p ON p.Run = u.Run
            WHERE u.Nombre_Usuario = :usuario
              AND u.Contrasena = SHA2(:clave, 256)
              AND u.Estado_de_Cuenta = 'Activa'
        """, {"usuario": nombre_usuario, "clave": clave})

        if len(cuenta) == 0:
            st.error("Usuario o contraseña incorrectos, o la cuenta no está activa.")
            return

        id_usuario = int(cuenta["Id_Usuario"][0])
        roles = consultar("""
            SELECT r.Nombre_de_Rol
            FROM Asignacion a
            JOIN Rol_Sistema r ON r.Id_Rol = a.Id_Rol
            WHERE a.Id_Usuario = :id
        """, {"id": id_usuario})

        if len(roles) == 0:
            st.error("La cuenta no tiene roles asignados.")
            return

        # Se guarda el usuario en la sesión (así Streamlit "recuerda" que ya ingresó).
        st.session_state["id_usuario"] = id_usuario
        st.session_state["usuario"] = cuenta["Nombre_Usuario"][0]
        st.session_state["nombre"] = cuenta["Nombre"][0]
        st.session_state["roles"] = list(roles["Nombre_de_Rol"])
        st.rerun()


def paginas_permitidas(roles):
    """Junta las páginas de todos los roles del usuario, sin repetir."""
    paginas = []
    for rol in roles:
        for pagina in PAGINAS_POR_ROL[rol]:
            if pagina not in paginas:
                paginas.append(pagina)
    return paginas


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
if "usuario" not in st.session_state:
    pantalla_login()
else:
    roles = st.session_state["roles"]
    puede_editar = "Administrador" in roles     # solo el Administrador crea/modifica/desactiva

    st.sidebar.subheader(st.session_state["nombre"])
    st.sidebar.write(f"Usuario: {st.session_state['usuario']}")
    st.sidebar.write(f"Rol: {', '.join(roles)}")
    pagina = st.sidebar.radio("Menú", paginas_permitidas(roles))
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    if pagina == "Panel de información":
        dashboard.mostrar()
    elif pagina == "Inscripciones":
        inscripciones.mostrar()
    elif pagina == "Parques":
        parques.mostrar(puede_editar)
    elif pagina == "Especies":
        especies.mostrar(puede_editar)
    elif pagina == "Usuarios":
        usuarios.mostrar()
