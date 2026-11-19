"""
generar_datos.py - Poblamiento sintético de la base de datos (Faker + random)
Proyecto TDFI103 Fase 2 - Caso 1: Gestión de Parques Naturales - Grupo 8

Qué hace:
  1. Inventa datos coherentes para todas las tablas.
  2. Escribe los INSERT en  sql/2_datos.sql
  3. Arma el script integral  sql/script_integral.sql  juntando:
        sql/1_estructura.sql + sql/2_datos.sql + sql/3_vistas_procedimientos.sql

Reglas de negocio que respetan los datos:
  - Las especies solo aparecen en parques de su misma zona (norte, centro o sur).
  - Las excursiones solo se programan en áreas 'Operativa' con acceso 'Libre' o 'Restringido'.
  - Los inscritos de una excursión nunca superan su capacidad.
  - Excursiones ya realizadas (ene-oct 2026): asistencia 'Asiste' o 'No Asiste'.
  - Excursiones programadas (nov 2026 - ene 2027): asistencia 'Pendiente' (para probar el PMV).
  - Solo evalúan los visitantes que asistieron, y después de la excursión.

Cómo se usa (desde la carpeta pmv_parques):
    Con Docker (no hay que instalar Python ni Faker):
        docker compose run --rm generador
    Sin Docker (Python 3.12+):
        pip install -r requirements.txt
        python generador/generar_datos.py

Los datos son REPRODUCIBLES: como la semilla es fija y la versión de Faker está
fijada en requirements.txt, siempre se generan exactamente los mismos.
"""
import hashlib
import os
import random
from datetime import date, timedelta

from faker import Faker

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SEMILLA = 2026
random.seed(SEMILLA)
Faker.seed(SEMILLA)
fake = Faker("es_CL")

# La carpeta sql/ está al lado de la carpeta generador/ (se calcula desde este archivo,
# así funciona sin importar desde qué carpeta se ejecute el script)
CARPETA_SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql")
FECHA_CORTE = date(2026, 10, 31)     # último día con excursiones ya realizadas


# ---------------------------------------------------------------------------
# Funciones de apoyo
# ---------------------------------------------------------------------------
def fecha_al_azar(desde, hasta):
    """Devuelve una fecha al azar entre 'desde' y 'hasta'."""
    dias = (hasta - desde).days
    return desde + timedelta(days=random.randint(0, dias))


def sin_tildes(texto):
    """Quita tildes y ñ para armar correos y nombres de usuario."""
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u",
                  "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", " ": ""}
    for letra, nueva in reemplazos.items():
        texto = texto.replace(letra, nueva)
    return texto


def rut_con_digito(numero):
    """Calcula el dígito verificador de un RUT chileno (módulo 11)."""
    suma = 0
    factor = 2
    for digito in reversed(str(numero)):
        suma = suma + int(digito) * factor
        factor = factor + 1
        if factor == 8:
            factor = 2
    resto = 11 - (suma % 11)
    if resto == 11:
        dv = "0"
    elif resto == 10:
        dv = "K"
    else:
        dv = str(resto)
    return f"{numero}-{dv}"


def encriptar(clave):
    """Mismo resultado que la función SHA2(clave, 256) de MySQL."""
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def valor_sql(valor):
    """Convierte un valor de Python al formato que entiende SQL."""
    if valor is None:
        return "NULL"
    if isinstance(valor, (int, float)):
        return str(valor)
    texto = str(valor).replace("'", "''")    # una comilla simple se escribe '' en SQL
    return f"'{texto}'"


def escribir_inserts(archivo, tabla, columnas, filas):
    """Escribe los INSERT de una tabla, de a 100 filas por sentencia."""
    archivo.write(f"-- {tabla}: {len(filas)} filas\n")
    for inicio in range(0, len(filas), 100):
        grupo = filas[inicio:inicio + 100]
        archivo.write(f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES\n")
        lineas = []
        for fila in grupo:
            lineas.append("(" + ", ".join(valor_sql(v) for v in fila) + ")")
        archivo.write(",\n".join(lineas) + ";\n\n")


# ===========================================================================
# 1. COMUNIDADES (zona: N = norte, C = centro, S = sur)
# ===========================================================================
COMUNIDADES = [
    ("CA-01", "Comunidad Altiplano Norte", "Region de Arica y Parinacota", "Servicio de Biodiversidad Regional", "N"),
    ("CA-02", "Comunidad Desierto de Atacama", "Region de Antofagasta", "Direccion Regional de Conservacion", "N"),
    ("CA-03", "Comunidad Valle del Elqui", "Region de Coquimbo", "Agencia de Patrimonio Natural", "N"),
    ("CA-04", "Comunidad Costa Central", "Region de Valparaiso", "Agencia de Patrimonio Natural", "C"),
    ("CA-05", "Comunidad Cordillera Metropolitana", "Region Metropolitana", "Servicio de Biodiversidad Regional", "C"),
    ("CA-06", "Comunidad Valle del Maule", "Region del Maule", "Corporacion de Areas Protegidas", "C"),
    ("CA-07", "Comunidad Cordillera de Nahuelbuta", "Region del Biobio", "Corporacion de Areas Protegidas", "S"),
    ("CA-08", "Comunidad Lagos del Sur", "Region de Los Lagos", "Direccion Regional de Conservacion", "S"),
]

filas_comunidad = []
for c in COMUNIDADES:
    filas_comunidad.append((c[0], c[1], c[2], c[3]))

# ===========================================================================
# 2. PARQUES
# popularidad: los parques más populares reciben más excursiones y visitantes
# ===========================================================================
PARQUES = [
    # (nombre, comunidad principal, estado de conservación, popularidad)
    ("Parque Natural Altos del Salar", "CA-02", "Bueno", 1.0),
    ("Parque Natural Quebrada Seca", "CA-02", "Regular", 0.6),
    ("Parque Natural Pampa del Tamarugal", "CA-01", "Critico", 0.5),
    ("Parque Natural Laguna Escondida", "CA-03", "Bueno", 1.3),
    ("Parque Natural Costa Rocosa", "CA-04", "Bueno", 1.8),
    ("Parque Natural Isla Bruma", "CA-04", "Regular", 0.9),
    ("Parque Natural Cordillera Alta", "CA-05", "Regular", 1.6),
    ("Reserva Valle Verde", "CA-06", "Critico", 0.7),
    ("Parque Natural Cumbres del Maule", "CA-06", "Regular", 1.0),
    ("Parque Natural Nevado Azul", "CA-06", "Bueno", 1.2),
    ("Parque Natural Valle del Condor", "CA-07", "Regular", 0.8),
    ("Parque Natural Sierra de Nahuelbuta", "CA-07", "Bueno", 1.1),
    ("Parque Natural Bosque Nativo Sur", "CA-08", "Bueno", 1.7),
    ("Parque Natural Humedal Austral", "CA-08", "Critico", 0.6),
    ("Parque Natural Rios del Sur", "CA-08", "Regular", 1.4),
]

parques = []            # lista de diccionarios (se usan después para las otras tablas)
correlativo_por_anio = {}
for nombre, comunidad, estado, popularidad in PARQUES:
    # buscar la región y la zona de la comunidad
    for c in COMUNIDADES:
        if c[0] == comunidad:
            region = c[2]
            zona = c[4]
    anio = random.randint(1967, 2020)
    correlativo_por_anio[anio] = correlativo_por_anio.get(anio, 0) + 1
    parques.append({
        "anio": anio,
        "correlativo": correlativo_por_anio[anio],
        "nombre": nombre,
        "fecha": fecha_al_azar(date(anio, 1, 1), date(anio, 12, 31)),
        "superficie": round(random.uniform(8000, 160000), 2),
        "presupuesto": random.randint(12, 85) * 10000000,
        "estado": estado,
        "region": region,
        "comunidad": comunidad,
        "zona": zona,
        "popularidad": popularidad,
    })

filas_parque = []
for p in parques:
    filas_parque.append((p["anio"], p["correlativo"], p["nombre"], p["fecha"], p["superficie"],
                         p["presupuesto"], p["estado"], p["region"], "Si", p["comunidad"]))

# Participación: 2 de cada 3 parques pertenecen 100% a su comunidad principal;
# el resto se comparte con otra comunidad de la misma zona.
filas_participacion = []
for p in parques:
    otras = []
    for c in COMUNIDADES:
        if c[4] == p["zona"] and c[0] != p["comunidad"]:
            otras.append(c[0])
    if random.random() < 0.66 or len(otras) == 0:
        filas_participacion.append((p["comunidad"], p["anio"], p["correlativo"], 100))
    else:
        porcentaje = random.choice([50, 60, 70, 80])
        filas_participacion.append((p["comunidad"], p["anio"], p["correlativo"], porcentaje))
        filas_participacion.append((random.choice(otras), p["anio"], p["correlativo"], 100 - porcentaje))

# ===========================================================================
# 3. ÁREAS: 3 o 4 por parque. Las 2 primeras siempre quedan habilitadas
#    para excursiones (Operativa + acceso Libre o Restringido).
# ===========================================================================
NOMBRES_AREA = {
    "N": ["Salar", "Quebrada Honda", "Mirador Central", "Pampa", "Canadon", "Oasis", "Laguna Altiplanica"],
    "C": ["Sendero Alto", "Acantilado", "Bosque Esclerofilo", "Laguna Norte", "Mirador Central", "Praderas", "Estero"],
    "S": ["Bosque Sur", "Ribera", "Cascada", "Humedal", "Turbera", "Sendero Alto", "Lago Interior"],
}

areas = []
for p in parques:
    cantidad = random.choice([3, 4])
    nombres = random.sample(NOMBRES_AREA[p["zona"]], cantidad)     # sin repetir dentro del parque
    for numero in range(1, cantidad + 1):
        if numero <= 2:
            acceso = random.choice(["Libre", "Libre", "Restringido"])
            estado = "Operativa"
        else:
            acceso = random.choice(["Libre", "Restringido", "Solo Investigacion"])
            estado = random.choice(["Operativa", "Mantencion", "Cerrada"])
        areas.append({
            "parque": p,
            "numero": numero,
            "nombre": nombres[numero - 1],
            "extension": round(random.uniform(150, 6000), 2),
            "acceso": acceso,
            "estado": estado,
            "tasa_asistencia": random.uniform(0.60, 0.95),   # cuántos inscritos suelen asistir
            "calidad": random.uniform(4.0, 6.0),              # nota "base" de las excursiones del área
        })

filas_area = []
for a in areas:
    filas_area.append((a["parque"]["anio"], a["parque"]["correlativo"], a["numero"], a["nombre"],
                       a["extension"], a["acceso"], a["estado"]))

# ===========================================================================
# 4. ESPECIES Y SUBTIPOS (catálogo real de Chile, revisado a mano)
# ===========================================================================
VEGETALES = [  # (nombre científico, nombre común, estado, floración, zonas donde vive)
    ("Araucaria araucana", "Araucaria", "En Peligro", "Conos maduran en otono (mar-may)", "S"),
    ("Nothofagus obliqua", "Roble", "Preocupacion Menor", "Floracion en primavera (sep-nov)", "CS"),
    ("Nothofagus dombeyi", "Coigue", "Preocupacion Menor", "Floracion en primavera (sep-nov)", "S"),
    ("Nothofagus pumilio", "Lenga", "Preocupacion Menor", "Floracion en primavera (oct-nov)", "S"),
    ("Nothofagus antarctica", "Nirre", "Preocupacion Menor", "Floracion en primavera (oct-nov)", "S"),
    ("Fitzroya cupressoides", "Alerce", "En Peligro", "Conos en primavera (oct-dic)", "S"),
    ("Austrocedrus chilensis", "Cipres de la cordillera", "Vulnerable", "Conos en primavera (sep-nov)", "CS"),
    ("Drimys winteri", "Canelo", "Preocupacion Menor", "Floracion en primavera (sep-dic)", "CS"),
    ("Eucryphia cordifolia", "Ulmo", "Preocupacion Menor", "Floracion estival (ene-mar)", "S"),
    ("Laurelia sempervirens", "Laurel chileno", "Preocupacion Menor", "Floracion en primavera (sep-oct)", "CS"),
    ("Aextoxicon punctatum", "Olivillo", "Preocupacion Menor", "Floracion invernal (jul-sep)", "CS"),
    ("Peumus boldus", "Boldo", "Preocupacion Menor", "Floracion invernal (jun-ago)", "C"),
    ("Quillaja saponaria", "Quillay", "Preocupacion Menor", "Floracion en primavera (oct-dic)", "C"),
    ("Cryptocarya alba", "Peumo", "Preocupacion Menor", "Floracion estival (dic-feb)", "C"),
    ("Lithraea caustica", "Litre", "Preocupacion Menor", "Floracion en primavera (sep-dic)", "C"),
    ("Jubaea chilensis", "Palma chilena", "Vulnerable", "Floracion en primavera (oct-dic)", "C"),
    ("Puya chilensis", "Chagual", "Preocupacion Menor", "Floracion en primavera (oct-nov)", "C"),
    ("Beilschmiedia miersii", "Belloto del norte", "Vulnerable", "Floracion en primavera (sep-nov)", "C"),
    ("Gunnera tinctoria", "Nalca", "Preocupacion Menor", "Floracion en primavera (oct-dic)", "S"),
    ("Fuchsia magellanica", "Chilco", "Preocupacion Menor", "Floracion estival (dic-mar)", "S"),
    ("Lapageria rosea", "Copihue", "Preocupacion Menor", "Floracion otonal (mar-jun)", "S"),
    ("Embothrium coccineum", "Notro", "Preocupacion Menor", "Floracion en primavera (oct-dic)", "S"),
    ("Lomatia hirsuta", "Radal", "Preocupacion Menor", "Floracion en primavera (oct-dic)", "CS"),
    ("Luma apiculata", "Arrayan", "Preocupacion Menor", "Floracion estival (ene-mar)", "S"),
    ("Gevuina avellana", "Avellano chileno", "Preocupacion Menor", "Floracion otonal (mar-may)", "S"),
    ("Pilgerodendron uviferum", "Cipres de las Guaitecas", "Vulnerable", "Conos en primavera (sep-nov)", "S"),
    ("Prosopis tamarugo", "Tamarugo", "En Peligro", "Floracion en primavera (sep-nov)", "N"),
    ("Polylepis tarapacana", "Queñoa", "Casi Amenazada", "Floracion estival (dic-feb)", "N"),
    ("Azorella compacta", "Llareta", "Vulnerable", "Floracion estival (dic-feb)", "N"),
    ("Copiapoa cinerea", "Copiapoa", "Vulnerable", "Floracion en primavera (sep-nov)", "N"),
]
ANIMALES = [  # (nombre científico, nombre común, estado, alimentación, período de celo, zonas)
    ("Pudu puda", "Pudu", "Vulnerable", "Herbivoro", "Otono", "S"),
    ("Hippocamelus bisulcus", "Huemul", "En Peligro", "Herbivoro", "Otono", "S"),
    ("Lama guanicoe", "Guanaco", "Preocupacion Menor", "Herbivoro", "Verano", "NCS"),
    ("Vicugna vicugna", "Vicuna", "Preocupacion Menor", "Herbivoro", "Verano", "N"),
    ("Puma concolor", "Puma", "Casi Amenazada", "Carnivoro", "Anual", "NCS"),
    ("Leopardus guigna", "Guina", "Vulnerable", "Carnivoro", "Invierno", "CS"),
    ("Leopardus colocolo", "Gato colocolo", "Casi Amenazada", "Carnivoro", "Primavera", "NC"),
    ("Lycalopex culpaeus", "Zorro culpeo", "Preocupacion Menor", "Omnivoro", "Invierno", "NCS"),
    ("Lycalopex griseus", "Zorro chilla", "Preocupacion Menor", "Omnivoro", "Invierno", "CS"),
    ("Lycalopex fulvipes", "Zorro de Darwin", "En Peligro", "Omnivoro", "Invierno", "S"),
    ("Lontra provocax", "Huillin", "En Peligro", "Piscivoro", "Anual", "S"),
    ("Dromiciops gliroides", "Monito del monte", "Casi Amenazada", "Insectivoro", "Primavera", "S"),
    ("Chinchilla lanigera", "Chinchilla", "En Peligro", "Herbivoro", "Invierno", "N"),
    ("Lagidium viscacia", "Vizcacha", "Preocupacion Menor", "Herbivoro", "Otono", "NC"),
    ("Octodon degus", "Degu", "Preocupacion Menor", "Herbivoro", "Otono", "C"),
    ("Vultur gryphus", "Condor andino", "Vulnerable", "Carronero", "Primavera", "NCS"),
    ("Campephilus magellanicus", "Carpintero negro", "Preocupacion Menor", "Insectivoro", "Primavera", "S"),
    ("Phoenicopterus chilensis", "Flamenco chileno", "Casi Amenazada", "Omnivoro", "Verano", "N"),
    ("Spheniscus humboldti", "Pinguino de Humboldt", "Vulnerable", "Piscivoro", "Primavera", "NC"),
    ("Cygnus melancoryphus", "Cisne de cuello negro", "Preocupacion Menor", "Herbivoro", "Primavera", "CS"),
    ("Enicognathus leptorhynchus", "Choroy", "Preocupacion Menor", "Herbivoro", "Primavera", "S"),
    ("Cyanoliseus patagonus", "Loro tricahue", "Casi Amenazada", "Herbivoro", "Primavera", "C"),
    ("Rhea pennata", "Nandu", "Casi Amenazada", "Omnivoro", "Primavera", "N"),
    ("Rhinoderma darwinii", "Ranita de Darwin", "En Peligro", "Insectivoro", "Primavera", "S"),
    ("Calyptocephalella gayi", "Rana chilena", "Vulnerable", "Carnivoro", "Invierno", "CS"),
    ("Liolaemus tenuis", "Lagartija esbelta", "Preocupacion Menor", "Insectivoro", "Primavera", "CS"),
    ("Philodryas chamissonis", "Culebra de cola larga", "Preocupacion Menor", "Carnivoro", "Primavera", "NC"),
    ("Pteroptochos tarnii", "Hued-hued del sur", "Preocupacion Menor", "Insectivoro", "Primavera", "S"),
    ("Scelorchilus rubecula", "Chucao", "Preocupacion Menor", "Insectivoro", "Primavera", "S"),
    ("Strix rufipes", "Concon", "Preocupacion Menor", "Carnivoro", "Primavera", "S"),
]
MINERALES = [  # (denominación, nombre común, estado, roca, cristales, zonas)
    ("Cuarzo SiO2", "Cuarzo", "Preocupacion Menor", "Granito", "Cuarzo", "NCS"),
    ("Calcita CaCO3", "Calcita", "Preocupacion Menor", "Caliza", "Calcita", "NCS"),
    ("Halita NaCl", "Halita", "Preocupacion Menor", "Evaporita", "Halita", "N"),
    ("Yeso CaSO4-2H2O", "Yeso", "Preocupacion Menor", "Evaporita", "Yeso", "N"),
    ("Ulexita NaCaB5O9-8H2O", "Ulexita", "Vulnerable", "Evaporita", "Ulexita", "N"),
    ("Atacamita Cu2Cl(OH)3", "Atacamita", "Vulnerable", "Porfido cuprifero", "Atacamita", "N"),
    ("Crisocola (Cu,Al)2H2Si2O5(OH)4", "Crisocola", "Preocupacion Menor", "Porfido cuprifero", None, "NC"),
    ("Malaquita Cu2CO3(OH)2", "Malaquita", "Casi Amenazada", "Porfido cuprifero", "Malaquita", "NC"),
    ("Azufre nativo S", "Azufre", "Preocupacion Menor", "Roca volcanica", "Azufre", "N"),
    ("Obsidiana volcanica", "Obsidiana", "Casi Amenazada", "Obsidiana", None, "NCS"),
    ("Basalto columnar", "Basalto", "Preocupacion Menor", "Basalto", None, "CS"),
    ("Andesita volcanica", "Andesita", "Preocupacion Menor", "Andesita", None, "NCS"),
    ("Granodiorita", "Granodiorita", "Preocupacion Menor", "Granodiorita", None, "CS"),
    ("Lapislazuli (Lazurita)", "Lapislazuli", "En Peligro", "Marmol", "Lazurita", "N"),
    ("Pirita FeS2", "Pirita", "Preocupacion Menor", "Pizarra", "Pirita", "NCS"),
    ("Magnetita Fe3O4", "Magnetita", "Preocupacion Menor", "Basalto", "Magnetita", "N"),
]
SIN_CLASIFICAR = [  # hongos, líquenes y algas: no son vegetal, animal ni mineral (generalización PARCIAL)
    ("Cyttaria espinosae", "Digueñe", "Preocupacion Menor", "S"),
    ("Morchella conica", "Morchella", "Preocupacion Menor", "CS"),
    ("Durvillaea antarctica", "Cochayuyo", "Preocupacion Menor", "CS"),
    ("Macrocystis pyrifera", "Huiro", "Casi Amenazada", "NCS"),
    ("Sphagnum magellanicum", "Musgo pompon", "Vulnerable", "S"),
    ("Xanthoria parietina", "Liquen anaranjado", "Preocupacion Menor", "NCS"),
    ("Rhizocarpon geographicum", "Liquen geografico", "Preocupacion Menor", "NC"),
    ("Cladonia rangiferina", "Liquen de los renos", "Preocupacion Menor", "S"),
    ("Gracilaria chilensis", "Pelillo", "Casi Amenazada", "CS"),
    ("Usnea barbata", "Barba de viejo", "Preocupacion Menor", "S"),
]

especies = []
filas_especie, filas_vegetal, filas_animal, filas_mineral = [], [], [], []
id_especie = 0

for v in VEGETALES:
    id_especie += 1
    especies.append({"id": id_especie, "tipo": "Vegetal", "estado": v[2], "zonas": v[4]})
    filas_especie.append((id_especie, v[0], v[1], v[2], fecha_al_azar(date(2015, 1, 1), date(2025, 12, 31)), "Vegetal", "Si"))
    filas_vegetal.append((id_especie, v[3]))

for an in ANIMALES:
    id_especie += 1
    especies.append({"id": id_especie, "tipo": "Animal", "estado": an[2], "zonas": an[5]})
    filas_especie.append((id_especie, an[0], an[1], an[2], fecha_al_azar(date(2015, 1, 1), date(2025, 12, 31)), "Animal", "Si"))
    filas_animal.append((id_especie, an[3], an[4]))

for m in MINERALES:
    id_especie += 1
    especies.append({"id": id_especie, "tipo": "Mineral", "estado": m[2], "zonas": m[5]})
    filas_especie.append((id_especie, m[0], m[1], m[2], fecha_al_azar(date(2015, 1, 1), date(2025, 12, 31)), "Mineral", "Si"))
    filas_mineral.append((id_especie, m[3], m[4]))

for s in SIN_CLASIFICAR:
    id_especie += 1
    especies.append({"id": id_especie, "tipo": None, "estado": s[2], "zonas": s[3]})
    filas_especie.append((id_especie, s[0], s[1], s[2], fecha_al_azar(date(2015, 1, 1), date(2025, 12, 31)), None, "Si"))

# ===========================================================================
# 5. INVENTARIO: cada área registra entre 5 y 9 especies de su zona
# ===========================================================================
RANGO_CANTIDAD = {"Vegetal": (80, 3000), "Animal": (3, 350), "Mineral": (1, 60), None: (20, 1500)}
OBSERVACIONES_INVENTARIO = ["Poblacion estable", "Ligero descenso observado", "Aumento respecto al periodo anterior",
                            "Zona de dificil acceso, conteo parcial", "Presencia confirmada por fotografias",
                            "Se recomienda nuevo monitoreo", None, None]

filas_inventario = []
for a in areas:
    posibles = []
    for e in especies:
        if a["parque"]["zona"] in e["zonas"]:
            posibles.append(e)
    elegidas = random.sample(posibles, random.randint(5, 9))
    for e in elegidas:
        minimo, maximo = RANGO_CANTIDAD[e["tipo"]]
        if e["estado"] == "En Peligro":
            maximo = minimo + (maximo - minimo) // 4      # especies en peligro: menos individuos
        filas_inventario.append((a["parque"]["anio"], a["parque"]["correlativo"], a["numero"], e["id"],
                                 random.randint(minimo, maximo),
                                 fecha_al_azar(date(2025, 11, 1), FECHA_CORTE),
                                 random.choice(OBSERVACIONES_INVENTARIO)))

# ===========================================================================
# 6. PERSONAL (64 personas)
#   posiciones 0-49  -> trabajadores (0-5 son jefes de parque)
#   posiciones 38-49 -> además son investigadores (especialización SOLAPADA)
#   posiciones 50-63 -> solo investigadores
# ===========================================================================
FORMACION = ["Ingenieria Forestal", "Licenciatura en Biologia", "Tecnico en gestion ambiental",
             "Guardaparque certificado", "Geologo de campo", "Biologo marino",
             "Curso de primeros auxilios en terreno", "Ingenieria en Recursos Naturales", None]

personal = []
ruts_usados = []
for i in range(64):
    numero = random.randint(8000000, 24000000)
    while numero in ruts_usados:
        numero = random.randint(8000000, 24000000)
    ruts_usados.append(numero)

    es_trabajador = i < 50
    es_investigador = i >= 38
    if i < 6:
        labores = "Jefe de parque"
    elif not es_trabajador:
        labores = "Investigador asociado"
    elif es_investigador:
        labores = "Investigador de planta"
    else:
        labores = random.choice(["Guardaparque", "Guardaparque", "Tecnico en conservacion", "Brigadista", "Administrativo"])

    nombre = fake.first_name()
    apellido_p = fake.last_name()
    apellido_m = fake.last_name()
    correo = None
    if random.random() < 0.85:                    # el correo es opcional: ~15% no tiene
        correo = f"{sin_tildes(nombre).lower()}.{sin_tildes(apellido_p).lower()}{i + 1}@parques.cl"
    parque_de_trabajo = random.choice(parques)
    personal.append({
        "run": rut_con_digito(numero), "nombre": nombre, "apellido_p": apellido_p, "apellido_m": apellido_m,
        "nacimiento": fecha_al_azar(date(1966, 1, 1), date(2001, 12, 31)),
        "formacion": random.choice(FORMACION), "labores": labores,
        "calle": fake.street_name(), "numero": random.randint(10, 9999), "region": parque_de_trabajo["region"],
        "correo": correo, "trabajador": es_trabajador, "investigador": es_investigador,
        "parque": parque_de_trabajo,
    })

filas_personal = []
for p in personal:
    filas_personal.append((p["run"], p["nombre"], p["apellido_p"], p["apellido_m"], p["nacimiento"], p["formacion"],
                           p["labores"], p["calle"], p["numero"], p["region"], p["correo"]))

# Contacto (atributo multivaluado): 1 a 3 teléfonos por persona
filas_contacto = []
for p in personal:
    telefonos = []
    for _ in range(random.choice([1, 2, 2, 3])):
        telefono = f"+56 9 {random.randint(2000, 9999)} {random.randint(1000, 9999)}"
        if telefono not in telefonos:
            telefonos.append(telefono)
            filas_contacto.append((p["run"], telefono))

# Trabajadores (los jefes no tienen supervisor; el resto lo supervisa un jefe)
jefes = personal[0:6]
filas_trabajadores = []
for p in personal:
    if p["trabajador"]:
        if p in jefes:
            supervisor = None
        else:
            supervisor = random.choice(jefes)["run"]
        filas_trabajadores.append((p["run"], supervisor))

filas_investigacion = []
for p in personal:
    if p["investigador"]:
        filas_investigacion.append((p["run"],))

# Funciones y EJERCE: cada trabajador tiene una función principal según su cargo
# y algunos además tienen 1 o 2 funciones extra (para la vista R8).
FUNCIONES = [(1, "Gestion"), (2, "Vigilancia"), (3, "Conservacion"), (4, "Investigacion")]
FUNCION_PRINCIPAL = {"Jefe de parque": 1, "Administrativo": 1, "Guardaparque": 2, "Brigadista": 3,
                     "Tecnico en conservacion": 3, "Investigador de planta": 4}

filas_ejerce = []
for p in personal:
    if not p["trabajador"]:
        continue
    funciones = [FUNCION_PRINCIPAL[p["labores"]]]
    cantidad_extra = random.choice([0, 0, 0, 1, 1, 2])
    while len(funciones) < 1 + cantidad_extra:
        extra = random.choice([1, 2, 3])
        if extra not in funciones:
            funciones.append(extra)
    areas_del_parque = []
    for a in areas:
        if a["parque"] is p["parque"]:
            areas_del_parque.append(a)
    inicio_minimo = date(max(p["nacimiento"].year + 21, 2012), 1, 1)
    for f in funciones:
        for a in random.sample(areas_del_parque, random.choice([1, 1, 2])):
            filas_ejerce.append((p["run"], f, a["parque"]["anio"], a["parque"]["correlativo"], a["numero"],
                                 fecha_al_azar(inicio_minimo, date(2026, 6, 30))))

# ===========================================================================
# 7. USUARIOS Y ROLES (50 cuentas)
# ===========================================================================
ROLES = [(1, "Administrador"), (2, "Operador"), (3, "Analista")]
CLAVE_GENERAL = "Parques2026!"

guardaparques = []
for p in personal:
    if p["labores"] == "Guardaparque":
        guardaparques.append(p)
investigadores = []
for p in personal:
    if p["investigador"]:
        investigadores.append(p)

# 3 cuentas de demostración + 47 cuentas más elegidas al azar
con_cuenta = [jefes[0], guardaparques[0], investigadores[0]]
resto = []
for p in personal:
    if p not in con_cuenta:
        resto.append(p)
con_cuenta = con_cuenta + random.sample(resto, 47)

filas_usuario, filas_asignacion = [], []
for numero, p in enumerate(con_cuenta, start=1):
    if numero == 1:
        usuario, clave, estado, roles = "admin", "Admin2026!", "Activa", [1]
    elif numero == 2:
        usuario, clave, estado, roles = "operador", "Operador2026!", "Activa", [2]
    elif numero == 3:
        usuario, clave, estado, roles = "analista", "Analista2026!", "Activa", [3]
    else:
        usuario = f"{sin_tildes(p['nombre']).lower()}.{sin_tildes(p['apellido_p']).lower()}{numero}"[:30]
        clave = CLAVE_GENERAL
        estado = random.choice(["Activa"] * 9 + ["Inactiva", "Suspendida"])
        if p["labores"] == "Jefe de parque":
            roles = [1]
        elif p["labores"] == "Administrativo":
            roles = [2, 3]                       # cuenta con dos roles (relación N:M)
        elif p["investigador"]:
            roles = [3]
        else:
            roles = [2]
    filas_usuario.append((numero, p["run"], usuario, encriptar(clave), estado))
    for rol in roles:
        filas_asignacion.append((numero, rol))

# ===========================================================================
# 8. PROYECTOS CIENTÍFICOS
# ===========================================================================
PROYECTOS = [  # (nombre, zona, tipo de especie que estudia)
    ("Monitoreo de poblaciones de vicuna en el altiplano", "N", "Animal"),
    ("Conservacion de bosques de queñoa", "N", "Vegetal"),
    ("Ecologia reproductiva del flamenco chileno en salares", "N", "Animal"),
    ("Caracterizacion de evaporitas en salares andinos", "N", "Mineral"),
    ("Recuperacion del tamarugo en la pampa", "N", "Vegetal"),
    ("Mineralizacion cuprifera en quebradas del norte", "N", "Mineral"),
    ("Estado poblacional de la chinchilla", "N", "Animal"),
    ("Liquenes y algas del borde costero norte", "N", None),
    ("Regeneracion del bosque esclerofilo", "C", "Vegetal"),
    ("Conservacion de la palma chilena", "C", "Vegetal"),
    ("Uso de habitat del zorro culpeo en la zona central", "C", "Animal"),
    ("Monitoreo del loro tricahue", "C", "Animal"),
    ("Anfibios y reptiles de humedales centrales", "C", "Animal"),
    ("Geologia de afloramientos volcanicos", "C", "Mineral"),
    ("Impacto del turismo en la flora de senderos", "C", "Vegetal"),
    ("Algas pardas del litoral central", "C", None),
    ("Dinamica de bosques de araucaria", "S", "Vegetal"),
    ("Conservacion del alerce milenario", "S", "Vegetal"),
    ("Seguimiento del huemul en la cordillera austral", "S", "Animal"),
    ("Distribucion del pudu en bosque templado", "S", "Animal"),
    ("Estado poblacional del huillin en rios del sur", "S", "Animal"),
    ("Ecologia de la ranita de Darwin", "S", "Animal"),
    ("Hongos comestibles del bosque nativo", "S", None),
    ("Turberas y musgo pompon", "S", None),
    ("Aves de sotobosque: chucao y hued-hued", "S", "Animal"),
]

filas_proyecto, filas_estudia, filas_investiga, filas_asignar = [], [], [], []
for id_proyecto, (nombre, zona, tipo) in enumerate(PROYECTOS, start=1):
    inicio = fecha_al_azar(date(2019, 1, 1), date(2026, 6, 30))
    estado = random.choice(["En curso", "En curso", "En curso", "Finalizado", "Suspendido"])
    termino = None
    if estado != "En curso":
        termino = min(inicio + timedelta(days=random.randint(180, 1200)), FECHA_CORTE)
    filas_proyecto.append((id_proyecto, nombre, inicio, termino, estado))

    # especies estudiadas: del tipo y la zona del proyecto
    candidatas = []
    for e in especies:
        if e["tipo"] == tipo and zona in e["zonas"]:
            candidatas.append(e)
    for e in random.sample(candidatas, min(len(candidatas), random.randint(2, 5))):
        filas_investiga.append((id_proyecto, e["id"]))

    # investigadores del proyecto (1 a 5)
    for p in random.sample(investigadores, random.choice([1, 2, 2, 3, 3, 4, 5])):
        filas_estudia.append((id_proyecto, p["run"]))

    # áreas donde se desarrolla (1 a 3 áreas de parques de la zona)
    areas_zona = []
    for a in areas:
        if a["parque"]["zona"] == zona:
            areas_zona.append(a)
    for a in random.sample(areas_zona, random.randint(1, 3)):
        filas_asignar.append((id_proyecto, a["parque"]["anio"], a["parque"]["correlativo"], a["numero"]))

# ===========================================================================
# 9. VISITANTES (220)
# ===========================================================================
visitantes = []
filas_visitante = []
for i in range(1, 221):
    nombre = fake.first_name()
    apellido = fake.last_name()
    id_visitante = f"V-{i:04d}"
    correo = f"{sin_tildes(nombre).lower()}.{sin_tildes(apellido).lower()}{i}@correo.cl"
    visitantes.append(id_visitante)
    filas_visitante.append((id_visitante, f"{nombre} {apellido}", correo))

# ===========================================================================
# 10. EXCURSIONES
#   160 realizadas entre enero y octubre de 2026 (más en verano)
#    20 programadas entre noviembre 2026 y enero 2027 (para el PMV)
# ===========================================================================
PESO_MES = [18, 18, 12, 9, 7, 5, 6, 6, 9, 10]       # enero ... octubre
MODALIDADES = ["Senderismo", "Observacion de Fauna", "Observacion Botanica", "Geologia", "Fotografia", "Educativa"]
HORARIOS = ["08:00:00", "09:30:00", "10:00:00", "14:00:00", "15:30:00"]

areas_habilitadas = []
for a in areas:
    if a["estado"] == "Operativa" and a["acceso"] in ("Libre", "Restringido"):
        areas_habilitadas.append(a)

pesos_parque = []
for p in parques:
    pesos_parque.append(p["popularidad"])

excursiones = []
for n in range(1, 181):
    parque = random.choices(parques, weights=pesos_parque)[0]     # los populares salen más veces
    opciones = []
    for a in areas_habilitadas:
        if a["parque"] is parque:
            opciones.append(a)
    if n <= 160:
        mes = random.choices(range(1, 11), weights=PESO_MES)[0]
        fecha = date(2026, mes, random.randint(1, 28))
        programada = False
    else:
        fecha = fecha_al_azar(date(2026, 11, 2), date(2027, 1, 31))
        programada = True
    excursiones.append({
        "codigo": f"EX-{n:03d}", "fecha": fecha, "hora": random.choice(HORARIOS),
        "modalidad": random.choice(MODALIDADES), "capacidad": random.choice([10, 15, 20, 20, 25, 30, 40]),
        "area": random.choice(opciones), "programada": programada,
    })

filas_excursion = []
for x in excursiones:
    a = x["area"]
    filas_excursion.append((x["codigo"], x["fecha"], x["hora"], x["modalidad"], x["capacidad"],
                            a["parque"]["anio"], a["parque"]["correlativo"], a["numero"]))

# ===========================================================================
# 11. INSCRIPCIONES (nunca más inscritos que la capacidad)
# ===========================================================================
OBSERVACIONES_INSCRIPCION = ["Primera visita", "Viaja en grupo familiar", "Trae equipo propio",
                             "Solicita transporte", "Requiere guia bilingue", None, None, None, None]

inscripciones = []          # se guardan para generar las evaluaciones
filas_inscripcion = []
id_inscripcion = 0
for x in excursiones:
    ocupacion = random.uniform(0.12, 0.45) * x["area"]["parque"]["popularidad"]
    if x["programada"]:
        ocupacion = ocupacion * 0.6                 # todavía quedan cupos libres
    inscritos = round(x["capacidad"] * ocupacion)
    inscritos = max(2, min(inscritos, x["capacidad"]))
    x["ocupacion"] = inscritos / x["capacidad"]

    for id_visitante in random.sample(visitantes, inscritos):
        id_inscripcion += 1
        if x["programada"]:
            asistencia = "Pendiente"
            fecha_inscripcion = min(x["fecha"] - timedelta(days=random.randint(1, 30)), date(2026, 11, 7))
        else:
            if random.random() < x["area"]["tasa_asistencia"]:
                asistencia = "Asiste"
            else:
                asistencia = "No Asiste"
            fecha_inscripcion = x["fecha"] - timedelta(days=random.randint(1, 30))
        inscripciones.append({"excursion": x, "visitante": id_visitante, "asistencia": asistencia})
        filas_inscripcion.append((id_inscripcion, x["codigo"], id_visitante, fecha_inscripcion, asistencia,
                                  random.choice(OBSERVACIONES_INSCRIPCION)))

# ===========================================================================
# 12. EVALUACIONES: solo quienes asistieron (55% de ellos evalúa).
#     Nota = calidad del área - castigo si la excursión iba muy llena + azar.
#     Así la pregunta R3 (visitantes vs evaluación) muestra una relación.
# ===========================================================================
COMENTARIOS_BUENOS = ["Excelente experiencia.", "El guia fue muy amable.", "Paisajes hermosos.",
                      "Actividad educativa muy completa.", None]
COMENTARIOS_REGULARES = ["Muy buena ruta.", "Buena experiencia en general.", "Un poco agotador.", None]
COMENTARIOS_MALOS = ["Grupo demasiado grande.", "Poca informacion sobre la fauna.", "Falta mejor senalizacion.", None]

filas_evaluacion = []
numero_evaluacion = {}      # correlativo de evaluaciones por excursión
for ins in inscripciones:
    if ins["asistencia"] != "Asiste" or random.random() > 0.55:
        continue
    x = ins["excursion"]
    nota = x["area"]["calidad"] - 2 * (x["ocupacion"] - 0.4) + random.uniform(-1.5, 1.5)
    nota = round(nota)
    nota = max(1, min(7, nota))
    if nota >= 6:
        comentario = random.choice(COMENTARIOS_BUENOS)
    elif nota >= 4:
        comentario = random.choice(COMENTARIOS_REGULARES)
    else:
        comentario = random.choice(COMENTARIOS_MALOS)
    numero_evaluacion[x["codigo"]] = numero_evaluacion.get(x["codigo"], 0) + 1
    fecha_evaluacion = min(x["fecha"] + timedelta(days=random.randint(0, 7)), FECHA_CORTE)
    filas_evaluacion.append((x["codigo"], numero_evaluacion[x["codigo"]], ins["visitante"],
                             fecha_evaluacion, nota, comentario))

# ===========================================================================
# 13. ESCRITURA DE LOS ARCHIVOS
#     El orden respeta las claves foráneas: primero las tablas "padre".
# ===========================================================================
TABLAS = [
    ("Comunidad_Autonoma", ["Codigo", "Nombre_Comunidad", "Region_Administrativa", "Organismo_Responsable"],
     filas_comunidad),
    ("Parque_Natural", ["Anio_de_Declaracion", "Numero_Correlativo", "Nombre_Parque", "Fecha_de_Declaracion",
                        "Superficie_Total", "Presupuesto_Anual", "Estado_de_Conservacion", "Ubicacion", "Activo",
                        "Codigo_Comunidad"], filas_parque),
    ("Participacion_Comunidad", ["Codigo_Comunidad", "Anio_de_Declaracion", "Numero_Correlativo",
                                 "Porcentaje_Territorial"], filas_participacion),
    ("Area", ["Anio_de_Declaracion", "Numero_Correlativo", "Numero_Interno", "Nombre_de_Area", "Extension",
              "Nivel_Acceso", "Estado_Operativo"], filas_area),
    ("Especie", ["Id_Especie", "Denominacion_Cientifica", "Nombre_Vulgar", "Estado_de_Conservacion",
                 "Fecha_Especie", "Tipo_Especie", "Activo"], filas_especie),
    ("Especie_Vegetal", ["Id_Especie", "Antecedentes_Floracion"], filas_vegetal),
    ("Especie_Animal", ["Id_Especie", "Alimentacion", "Periodo_Celo"], filas_animal),
    ("Especie_Mineral", ["Id_Especie", "Roca", "Cristales"], filas_mineral),
    ("Inventario_Especie", ["Anio_de_Declaracion", "Numero_Correlativo", "Numero_Interno", "Id_Especie",
                            "Cantidad_Inventariada", "Fecha_Ultimo_Monitoreo", "Observaciones_Inventariado"],
     filas_inventario),
    ("Personal", ["Run", "Primer_Nombre", "Apellido_Paterno", "Apellido_Materno", "Fecha_Nacimiento",
                  "Antecedentes_Personales", "Labores", "Calle", "Numero", "Region", "Correo_Electronico"],
     filas_personal),
    ("Contacto", ["Run", "Contacto"], filas_contacto),
    ("Trabajadores", ["Run", "Run_Supervisor"], filas_trabajadores),
    ("Investigacion", ["Run"], filas_investigacion),
    ("Funcion", ["Id_Funcion", "Nombre_Funcion"], FUNCIONES),
    ("Ejerce", ["Run", "Id_Funcion", "Anio_de_Declaracion", "Numero_Correlativo", "Numero_Interno",
                "Fecha_Inicio"], filas_ejerce),
    ("Rol_Sistema", ["Id_Rol", "Nombre_de_Rol"], ROLES),
    ("Usuario", ["Id_Usuario", "Run", "Nombre_Usuario", "Contrasena", "Estado_de_Cuenta"], filas_usuario),
    ("Asignacion", ["Id_Usuario", "Id_Rol"], filas_asignacion),
    ("Proyecto_Cientifico", ["Id_Proyecto", "Nombre_Proyecto", "Fecha_Inicio", "Fecha_Termino", "Estado"],
     filas_proyecto),
    ("Estudia", ["Id_Proyecto", "Run"], filas_estudia),
    ("Investiga", ["Id_Proyecto", "Id_Especie"], filas_investiga),
    ("Asignar", ["Id_Proyecto", "Anio_de_Declaracion", "Numero_Correlativo", "Numero_Interno"], filas_asignar),
    ("Visitantes", ["Id_Visitante", "Nombre_Visitante", "Correo_Electronico"], filas_visitante),
    ("Excursiones", ["Registro_Codigo", "Fecha_Excursiones", "Horario_Excursiones", "Modalidad", "Capacidad",
                     "Anio_de_Declaracion", "Numero_Correlativo", "Numero_Interno"], filas_excursion),
    ("Inscripcion", ["Id_Inscripcion", "Registro_Codigo", "Id_Visitante", "Fecha_Inscripcion", "Asistencia",
                     "Observaciones"], filas_inscripcion),
    ("Evaluacion", ["Registro_Codigo", "Numero_Evaluacion", "Id_Visitante", "Fecha_Evaluacion", "Calificacion",
                    "Comentario"], filas_evaluacion),
]

ruta_datos = os.path.join(CARPETA_SQL, "2_datos.sql")
with open(ruta_datos, "w", encoding="utf-8") as archivo:
    archivo.write("-- =========================================================================\n")
    archivo.write(f"-- 4. INSERCIÓN DE DATOS (generado con generador/generar_datos.py, semilla {SEMILLA})\n")
    archivo.write("-- =========================================================================\n")
    archivo.write("USE Sistema_Integral_Parques_Naturales;\n\n")
    for tabla, columnas, filas in TABLAS:
        escribir_inserts(archivo, tabla, columnas, filas)

# Script integral = estructura + datos + vistas y procedimientos
ruta_integral = os.path.join(CARPETA_SQL, "script_integral.sql")
with open(ruta_integral, "w", encoding="utf-8") as integral:
    for parte in ["1_estructura.sql", "2_datos.sql", "3_vistas_procedimientos.sql"]:
        with open(os.path.join(CARPETA_SQL, parte), encoding="utf-8") as archivo:
            integral.write(archivo.read())
        integral.write("\n\n")

print("Archivos generados: sql/2_datos.sql y sql/script_integral.sql")
print()
print(f"{'Tabla':<25} Filas")
for tabla, columnas, filas in TABLAS:
    print(f"{tabla:<25} {len(filas):>5}")
