"""
prueba_pmv.py - Prueba automática del PMV (34 verificaciones) con streamlit.testing.

Simula a un usuario: login con cada rol, cuentas bloqueadas, inscripción con sus
validaciones, registro de asistencia, CRUD de parques y especies y administración
de usuarios. Después de cada acción revisa la base de datos con una consulta.

OJO: crea registros de prueba (un parque, especies, una inscripción). Después de
correrla, reiniciar la base:  docker compose down -v  y  docker compose up -d

Cómo ejecutarla (desde la carpeta pmv_parques, con docker compose ya levantado):
    docker cp ../pruebas/prueba_pmv.py parques_pmv:/tmp/prueba_pmv.py
    docker exec -w /app parques_pmv python /tmp/prueba_pmv.py
"""
import sys
sys.path.insert(0, "/app")
from streamlit.testing.v1 import AppTest
from db import consultar

T = 60
fallas = []


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        fallas.append(msg)


def login(usuario, clave):
    at = AppTest.from_file("/app/app.py", default_timeout=T)
    at.run()
    at.text_input[0].input(usuario)
    at.text_input[1].input(clave)
    at.button[0].click()
    at.run()
    return at


def ir(at, pagina):
    at.sidebar.radio[0].set_value(pagina)
    at.run()
    ok(len(at.exception) == 0, f"página '{pagina}' sin excepciones {[e.value for e in at.exception]}")
    return at


# --- Login ---
at = login("admin", "malaclave")
ok(len(at.error) == 1 and "usuario" not in at.session_state, "login con clave incorrecta rechazado")

inactiva = consultar("SELECT Nombre_Usuario FROM Usuario WHERE Estado_de_Cuenta <> 'Activa' LIMIT 1")["Nombre_Usuario"][0]
at = login(inactiva, "Parques2026!")
ok(len(at.error) == 1, f"cuenta no activa ({inactiva}) rechazada")

at = login("operador", "Operador2026!")
ok(list(at.sidebar.radio[0].options) == ["Panel de información", "Inscripciones"], f"menú operador {at.sidebar.radio[0].options}")

at = login("analista", "Analista2026!")
ok(list(at.sidebar.radio[0].options) == ["Panel de información", "Parques", "Especies"], f"menú analista {at.sidebar.radio[0].options}")
at = ir(at, "Parques")
ok(len(at.info) == 1 and len(at.main.radio) == 0 and len(at.main.button) == 0, "analista: parques solo lectura")

at = login("admin", "Admin2026!")
ok(len(at.sidebar.radio[0].options) == 5, f"menú admin {at.sidebar.radio[0].options}")
ok(len(at.exception) == 0, f"dashboard sin excepciones {[e.value for e in at.exception]}")
ok(len(at.get("plotly_chart")) == 4, f"dashboard con 4 gráficos ({len(at.get('plotly_chart'))})")
print("     métrica correlación:", [m.value for m in at.metric])

# filtro por parque en el dashboard
at.selectbox[0].set_value("Parque Natural Costa Rocosa")
at.run()
ok(len(at.exception) == 0, "dashboard filtrado por parque sin excepciones")

# --- Inscripciones ---
at = ir(at, "Inscripciones")
antes = consultar("SELECT COUNT(*) AS n FROM Inscripcion")["n"][0]
exc = at.selectbox[0].value
codigo = exc.split(" | ")[0]
libres = consultar("""SELECT v.Id_Visitante, v.Nombre_Visitante FROM Visitantes v
                      WHERE v.Id_Visitante NOT IN (SELECT Id_Visitante FROM Inscripcion WHERE Registro_Codigo = :c)
                      ORDER BY v.Nombre_Visitante LIMIT 1""", {"c": codigo})
etiqueta = libres["Id_Visitante"][0] + " | " + libres["Nombre_Visitante"][0]

# sin visitante -> error
at.button[0].click()
at.run()
ok(any("visitante" in e.value for e in at.error), "inscripción sin visitante rechazada")

at.selectbox[1].set_value(etiqueta)
at.text_input[0].input("Prueba automatizada")
at.button[0].click()
at.run()
despues = consultar("SELECT COUNT(*) AS n FROM Inscripcion")["n"][0]
ok(despues == antes + 1 and len(at.success) == 1, f"inscripción insertada ({antes}->{despues}) en {codigo}")
fila = consultar("SELECT Asistencia, Fecha_Inscripcion FROM Inscripcion WHERE Registro_Codigo=:c AND Id_Visitante=:v",
                 {"c": codigo, "v": libres["Id_Visitante"][0]})
ok(fila["Asistencia"][0] == "Pendiente", f"queda Pendiente, fecha {fila['Fecha_Inscripcion'][0]}")

# duplicada
at.selectbox[0].set_value(exc)
at.selectbox[1].set_value(etiqueta)
at.button[0].click()
at.run()
ok(any("ya está inscrito" in e.value for e in at.error), "inscripción duplicada rechazada")

# excursión llena: dejar una excursión al máximo y probar
llena = consultar("""SELECT x.Registro_Codigo, x.Capacidad,
                     (SELECT COUNT(*) FROM Inscripcion i WHERE i.Registro_Codigo=x.Registro_Codigo) AS n
                     FROM Excursiones x WHERE x.Fecha_Excursiones >= CURDATE() ORDER BY x.Registro_Codigo DESC LIMIT 1""")
cod_llena = llena["Registro_Codigo"][0]
from db import ejecutar
ejecutar("UPDATE Excursiones SET Capacidad = :c WHERE Registro_Codigo = :x", {"c": int(llena["n"][0]), "x": cod_llena})
at.run()
op = [o for o in at.selectbox[0].options if o.startswith(cod_llena)][0]
at.selectbox[0].set_value(op)
libre2 = consultar("""SELECT CONCAT(Id_Visitante,' | ',Nombre_Visitante) AS e FROM Visitantes
                      WHERE Id_Visitante NOT IN (SELECT Id_Visitante FROM Inscripcion WHERE Registro_Codigo=:c) LIMIT 1""",
                   {"c": cod_llena})["e"][0]
at.selectbox[1].set_value(libre2)
at.button[0].click()
at.run()
ok(any("cupos" in e.value for e in at.error), f"excursión llena {cod_llena} rechazada")
ejecutar("UPDATE Excursiones SET Capacidad = :c WHERE Registro_Codigo = :x", {"c": int(llena["Capacidad"][0]), "x": cod_llena})

# asistencia
pend = consultar("""SELECT COUNT(*) AS n FROM Inscripcion i JOIN Excursiones x ON x.Registro_Codigo=i.Registro_Codigo
                    WHERE i.Asistencia='Pendiente' AND x.Fecha_Excursiones <= CURDATE()""")["n"][0]
print("     pendientes de excursiones ya realizadas:", pend)
if pend > 0:
    insc = at.selectbox[2].value
    at.radio[0].set_value("Asiste")
    at.button[1].click()
    at.run()
    idi = int(insc.split(" | ")[0])
    ok(consultar("SELECT Asistencia FROM Inscripcion WHERE Id_Inscripcion=:i", {"i": idi})["Asistencia"][0] == "Asiste",
       f"asistencia registrada para inscripción {idi}")

# --- Parques ---
at = ir(at, "Parques")
at.text_input[0].input("Parque Natural Prueba")
at.text_input[1].input("Region de Prueba")
at.number_input[0].set_value(1500.0)
at.number_input[1].set_value(50000000)
at.button[0].click()
at.run()
nuevo = consultar("SELECT * FROM Parque_Natural WHERE Nombre_Parque='Parque Natural Prueba'")
ok(len(nuevo) == 1 and len(at.exception) == 0, f"parque creado {nuevo[['Anio_de_Declaracion','Numero_Correlativo']].values.tolist()}")
ok(len(consultar("SELECT * FROM Participacion_Comunidad WHERE Anio_de_Declaracion=:a AND Numero_Correlativo=:c",
                 {"a": int(nuevo['Anio_de_Declaracion'][0]), "c": int(nuevo['Numero_Correlativo'][0])})) == 1,
   "participación 100% creada")

at.radio[0].set_value("Modificar")
at.run()
rol = [o for o in at.selectbox[0].options if "Parque Natural Prueba" in o][0]
at.selectbox[0].set_value(rol)
at.run()
at.number_input[0].set_value(2500.0)
at.button[0].click()
at.run()
ok(float(consultar("SELECT Superficie_Total FROM Parque_Natural WHERE Nombre_Parque='Parque Natural Prueba'")["Superficie_Total"][0]) == 2500.0,
   "parque modificado")

at.radio[0].set_value("Desactivar o reactivar")
at.run()
op = [o for o in at.selectbox[0].options if "Parque Natural Prueba" in o][0]
at.selectbox[0].set_value(op)
at.button[0].click()
at.run()
ok(consultar("SELECT Activo FROM Parque_Natural WHERE Nombre_Parque='Parque Natural Prueba'")["Activo"][0] == "No",
   "parque desactivado")

# --- Especies ---
at = ir(at, "Especies")
at.radio[0].set_value("Crear")
at.run()
at.radio[1].set_value("Animal")
at.run()
at.text_input[0].input("Testus automaticus")
at.text_input[1].input("Bicho de prueba")
at.button[0].click()
at.run()
e = consultar("""SELECT e.Id_Especie, e.Tipo_Especie, a.Alimentacion FROM Especie e
                 JOIN Especie_Animal a ON a.Id_Especie=e.Id_Especie WHERE e.Denominacion_Cientifica='Testus automaticus'""")
ok(len(e) == 1, f"especie animal creada con subtipo {e.values.tolist()}")

at.radio[1].set_value("Mineral")
at.run()
at.text_input[0].input("Mineralus sinroca")
at.text_input[1].input("Mineral vacio")
at.button[0].click()
at.run()
ok(any("roca" in x.value for x in at.error), "mineral sin roca ni cristales rechazado")

at.radio[1].set_value("Sin clasificar")
at.run()
at.text_input[0].input("Fungus pruebus")
at.text_input[1].input("Hongo de prueba")
at.button[0].click()
at.run()
ok(len(consultar("SELECT * FROM Especie WHERE Denominacion_Cientifica='Fungus pruebus' AND Tipo_Especie IS NULL")) == 1,
   "especie sin clasificar creada con tipo NULL")

at.radio[0].set_value("Modificar")
at.run()
ok(len(at.exception) == 0, "modificar especie sin excepciones")
at.radio[0].set_value("Desactivar o reactivar")
at.run()
ok(len(at.exception) == 0, "desactivar especie sin excepciones")

# --- Usuarios ---
at = ir(at, "Usuarios")
op = [o for o in at.selectbox[0].options if o.split(" | ")[1] == "operador"][0]
at.selectbox[0].set_value(op)
at.selectbox[1].set_value("Suspendida")
at.button[0].click()
at.run()
ok(consultar("SELECT Estado_de_Cuenta FROM Usuario WHERE Nombre_Usuario='operador'")["Estado_de_Cuenta"][0] == "Suspendida",
   "cuenta operador suspendida")
at2 = login("operador", "Operador2026!")
ok("usuario" not in at2.session_state, "operador suspendido ya no entra")
ejecutar("UPDATE Usuario SET Estado_de_Cuenta='Activa' WHERE Nombre_Usuario='operador'")

op = [o for o in at.selectbox[0].options if o.split(" | ")[1] == "admin"][0]
at.selectbox[0].set_value(op)
at.selectbox[1].set_value("Inactiva")
at.button[0].click()
at.run()
ok(any("propia" in x.value for x in at.error), "admin no puede desactivarse a sí mismo")

print()
print("RESULTADO:", "TODO OK" if not fallas else f"{len(fallas)} FALLAS: {fallas}")
