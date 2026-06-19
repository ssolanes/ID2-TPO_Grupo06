# mongoBD.py
# Dataset completo de MongoDB para el proyecto WRC - TPO BDII 2026
#
# IMPORTANTE: Requiere MongoDB corriendo localmente en mongodb://localhost:27017/
# Instalación de dependencias: pip install pymongo
#
# Este dataset está sincronizado con neo4jBD.py:
#   - Los mismos 3 pilotos, copilotos, jefes de ingeniería, equipos, vehículos,
#     patrocinadores y rallies están presentes en ambas BDs.
#   - MongoDB genera automaticamente los _id al insertar este dataset.

from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    OperationFailure,
    BulkWriteError,
)
from datetime import datetime, timezone

# ─── Conexión ────────────────────────────────────────────────────────────────
print("=" * 60)
print("  WRC · MongoDB Dataset Loader")
print("=" * 60)

try:
    cliente = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=4000,
    )
    # Verificar conexión real
    cliente.admin.command("ping")
    print("✓  Conexión a MongoDB establecida (localhost:27017)")
except ServerSelectionTimeoutError:
    print("✗  ERROR: No se pudo conectar a MongoDB.")
    print("   Asegurate de que el servicio esté corriendo:")
    print("   Windows:  net start MongoDB")
    print("   Docker:   docker start mongo")
    exit(1)
except ConnectionFailure as e:
    print(f"✗  ERROR de conexión: {e}")
    exit(1)

db = cliente["mundial_rally"]
print(f"✓  Base de datos seleccionada: mundial_rally\n")

CAMPOS_RELACIONALES_MONGO = {
    "equipos": {
        "jefe_ingenieria_id",
        "pilotos_ids",
        "copilotos_ids",
        "vehiculos_ids",
        "patrocinadores_ids",
        "activo",
    },
    "pilotos": {
        "fecha_nacimiento",
        "equipo_id",
        "copiloto_id",
        "vehiculo_id",
        "numero_auto",
        "estado",
        "sponsors",
        "estadisticas",
    },
    "copiloto": {
        "fecha_nacimiento",
        "equipo_id",
        "piloto_id",
        "años_experiencia",
        "idiomas",
        "estado",
    },
    "vehiculos": {"equipo_id"},
    "patrocinador": {"pais_origen", "activo"},
    "jefe_ingenieria": {"equipo_id", "años_experiencia", "estado"},
    "rallies": {"campeonato", "equipos_participantes_ids"},
    "noticias_reportes": {"rally_id"},
    "resumenes_carrera": {"rally_id"},
}


def doc_mongo_limpio(coleccion, doc):
    campos = CAMPOS_RELACIONALES_MONGO.get(coleccion, set())
    return limpiar_ids_manuales(doc, campos)


def es_campo_id_manual(clave):
    return clave in {"id", "_id"} or clave.endswith("_id") or clave.endswith("_ids")


def limpiar_ids_manuales(valor, campos_extra=None):
    campos_extra = campos_extra or set()
    if isinstance(valor, dict):
        return {
            clave: limpiar_ids_manuales(subvalor)
            for clave, subvalor in valor.items()
            if clave not in campos_extra and not es_campo_id_manual(clave)
        }
    if isinstance(valor, list):
        return [limpiar_ids_manuales(item) for item in valor]
    return valor


# ─── Helper: limpiar e insertar colección ───────────────────────────────────
def cargar_coleccion(nombre: str, documentos: list):
    try:
        col = db[nombre]
        col.delete_many({})                    # limpiar datos anteriores
        resultado = col.insert_many([doc_mongo_limpio(nombre, doc) for doc in documentos])
        print(f"  ✓  {nombre:<25} → {len(resultado.inserted_ids)} documentos insertados")
    except BulkWriteError as bwe:
        print(f"  ✗  {nombre}: error de escritura masiva → {bwe.details}")
    except OperationFailure as e:
        print(f"  ✗  {nombre}: falla de operación → {e}")
    except Exception as e:
        print(f"  ✗  {nombre}: error inesperado → {e}")

# ─── Helper: fecha UTC ───────────────────────────────────────────────────────
def fecha(anio, mes, dia):
    return datetime(anio, mes, dia, tzinfo=timezone.utc)

# ══════════════════════════════════════════════════════════════════════════════
#  1. PATROCINADORES
#  Neo4j: s1=RedBull, s2=Pirelli, s3=Shell
# ══════════════════════════════════════════════════════════════════════════════
patrocinadores = [
    {
        "nombre":     "RedBull",
        "tipo":       "principal",
        "pais_origen":"Austria",
        "activo":     True,
    },
    {
        "nombre":     "Pirelli",
        "tipo":       "tecnico",
        "pais_origen":"Italia",
        "activo":     True,
    },
    {
        "nombre":     "Shell",
        "tipo":       "tecnico",
        "pais_origen":"Países Bajos",
        "activo":     True,
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  2. JEFES DE INGENIERÍA
#  Neo4j: j1=Michael Ross (e1), j2=Santiago Rivas (e2), j3=Kenji Sato (e3)
# ══════════════════════════════════════════════════════════════════════════════
jefes_ingenieria = [
    {
        "nombre":           "Michael",
        "apellido":         "Ross",
        "especialidad":     "Motores",
        "equipo_id":        "eq_monster",
        "años_experiencia": 12,
        "email":            "m.ross@monsterrally.com",
        "telefono":         "+1-555-0101",
        "certificaciones":  ["FIA Technical Delegate", "SAE Motorsport Engineering"],
        "estado":           "activo",
    },
    {
        "nombre":           "Santiago",
        "apellido":         "Rivas",
        "especialidad":     "Suspensión",
        "equipo_id":        "eq_andes",
        "años_experiencia": 8,
        "email":            "s.rivas@andesmotorsport.com.ar",
        "telefono":         "+54-11-5555-0202",
        "certificaciones":  ["FIA Homologation Specialist"],
        "estado":           "activo",
    },
    {
        "nombre":           "Kenji",
        "apellido":         "Sato",
        "especialidad":     "Aerodinámica",
        "equipo_id":        "eq_samurai",
        "años_experiencia": 10,
        "email":            "k.sato@samurairacing.jp",
        "telefono":         "+81-3-5555-0303",
        "certificaciones":  ["JSAE Motorsport Engineer", "FIA Aero Certification"],
        "estado":           "activo",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  3. EQUIPOS
#  Neo4j: e1=Monster Rally Team (USA), e2=Andes Motorsport (ARG), e3=Samurai Racing (JPN)
# ══════════════════════════════════════════════════════════════════════════════
equipos = [
    {
        "nombre":               "Monster Rally Team",
        "pais_base":            "Estados Unidos",
        "director":             "Brian Carter",
        "jefe_ingenieria_id":   "ji_ross",
        "pilotos_ids":          ["piloto_moretti"],
        "copilotos_ids":        ["copiloto_bellini"],
        "vehiculos_ids":        ["veh_puma_r1", "veh_fiesta_r2"],
        "patrocinadores_ids":   ["sponsor_redbull"],
        "activo":               True,
    },
    {
        "nombre":               "Andes Motorsport",
        "pais_base":            "Argentina",
        "director":             "Rodrigo Pereyra",
        "jefe_ingenieria_id":   "ji_rivas",
        "pilotos_ids":          ["piloto_benitez"],
        "copilotos_ids":        ["copiloto_suarez"],
        "vehiculos_ids":        ["veh_yaris_r1", "veh_corolla_r2"],
        "patrocinadores_ids":   ["sponsor_pirelli"],
        "activo":               True,
    },
    {
        "nombre":               "Samurai Racing",
        "pais_base":            "Japón",
        "director":             "Takeshi Mori",
        "jefe_ingenieria_id":   "ji_sato",
        "pilotos_ids":          ["piloto_tanaka"],
        "copilotos_ids":        ["copiloto_nakamura"],
        "vehiculos_ids":        ["veh_i20_r1", "veh_i20_r2"],
        "patrocinadores_ids":   ["sponsor_shell"],
        "activo":               True,
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  4. COPILOTOS
#  Neo4j: co1=Marco Bellini (e1), co2=Diego Suárez (e2), co3=Yuki Nakamura (e3)
# ══════════════════════════════════════════════════════════════════════════════
copilotos = [
    {
        "nombre":            "Marco",
        "apellido":          "Bellini",
        "fecha_nacimiento":  fecha(1994, 3, 15),
        "pais":              {"codigo": "IT", "nombre": "Italia"},
        "equipo_id":         "eq_monster",
        "piloto_id":         "piloto_moretti",
        "años_experiencia":  7,
        "idiomas":           ["italiano", "inglés", "francés"],
        "estado":            "activo",
    },
    {
        "nombre":            "Diego",
        "apellido":          "Suárez",
        "fecha_nacimiento":  fecha(1995, 8, 22),
        "pais":              {"codigo": "AR", "nombre": "Argentina"},
        "equipo_id":         "eq_andes",
        "piloto_id":         "piloto_benitez",
        "años_experiencia":  6,
        "idiomas":           ["español", "inglés"],
        "estado":            "activo",
    },
    {
        "nombre":            "Yuki",
        "apellido":          "Nakamura",
        "fecha_nacimiento":  fecha(1997, 11, 4),
        "pais":              {"codigo": "JP", "nombre": "Japón"},
        "equipo_id":         "eq_samurai",
        "piloto_id":         "piloto_tanaka",
        "años_experiencia":  5,
        "idiomas":           ["japonés", "inglés"],
        "estado":            "activo",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  5. PILOTOS
#  Neo4j: p1=Luca Moretti (ITA, 28), p2=Carlos Benítez (ARG, 31), p3=Hiro Tanaka (JPN, 26)
# ══════════════════════════════════════════════════════════════════════════════
pilotos = [
    {
        "nombre":           "Luca",
        "apellido":         "Moretti",
        "fecha_nacimiento": fecha(1997, 5, 10),   # edad 28 en 2026 (aprox.)
        "pais":             {"codigo": "IT", "nombre": "Italia"},
        "equipo_id":        "eq_monster",
        "copiloto_id":      "copiloto_bellini",
        "vehiculo_id":      "veh_puma_r1",
        "numero_auto":      1,
        "estado":           "activo",
        "sponsors":         ["sponsor_redbull"],
        "estadisticas": {
            "puntos":              142,
            "victorias":           3,
            "podios":              7,
            "rallies_disputados":  5,
        },
    },
    {
        "nombre":           "Carlos",
        "apellido":         "Benítez",
        "fecha_nacimiento": fecha(1994, 9, 3),    # edad 31 en 2026
        "pais":             {"codigo": "AR", "nombre": "Argentina"},
        "equipo_id":        "eq_andes",
        "copiloto_id":      "copiloto_suarez",
        "vehiculo_id":      "veh_yaris_r1",
        "numero_auto":      2,
        "estado":           "activo",
        "sponsors":         ["sponsor_pirelli"],
        "estadisticas": {
            "puntos":              118,
            "victorias":           2,
            "podios":              5,
            "rallies_disputados":  5,
        },
    },
    {
        "nombre":           "Hiro",
        "apellido":         "Tanaka",
        "fecha_nacimiento": fecha(1999, 12, 20),  # edad 26 en 2026
        "pais":             {"codigo": "JP", "nombre": "Japón"},
        "equipo_id":        "eq_samurai",
        "copiloto_id":      "copiloto_nakamura",
        "vehiculo_id":      "veh_i20_r1",
        "numero_auto":      3,
        "estado":           "activo",
        "sponsors":         ["sponsor_shell"],
        "estadisticas": {
            "puntos":              97,
            "victorias":           1,
            "podios":              4,
            "rallies_disputados":  5,
        },
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  6. VEHÍCULOS
#  Neo4j: v1=Ford Puma R1 (e1), v2=Ford Fiesta R2 (e1),
#         v3=Toyota GR Yaris R1 (e2), v4=Toyota Corolla R2 (e2),
#         v5=Hyundai i20 N R1 (e3), v6=Hyundai i20 R2 (e3)
# ══════════════════════════════════════════════════════════════════════════════
vehiculos = [
    {
        "equipo_id":        "eq_monster",
        "marca":            "Ford",
        "modelo":           "Puma Rally1",
        "anio":             2026,
        "tipo_combustible": "hibrido",
        "motor": {
            "hp":                500.0,
            "velocidad_punta_kmh": 210.0,
            "cilindrada_cc":     1600,
            "torque_nm":         425,
        },
        "configuracion": {
            "traccion":     "4WD",
            "transmision":  "secuencial 5 velocidades",
            "suspension":   "McPherson delantera / multilink trasera",
        },
        "estado_mecanico": {
            "ok":              True,
            "ultima_revision": fecha(2026, 7, 10),
        },
    },
    {
        "equipo_id":        "eq_monster",
        "marca":            "Ford",
        "modelo":           "Fiesta Rally2",
        "anio":             2026,
        "tipo_combustible": "nafta",
        "motor": {
            "hp":                470.0,
            "velocidad_punta_kmh": 205.0,
            "cilindrada_cc":     1600,
            "torque_nm":         400,
        },
        "configuracion": {
            "traccion":     "4WD",
            "transmision":  "secuencial 5 velocidades",
            "suspension":   "McPherson delantera / multilink trasera",
        },
        "estado_mecanico": {
            "ok":              True,
            "ultima_revision": fecha(2026, 7, 12),
        },
    },
    {
        "equipo_id":        "eq_andes",
        "marca":            "Toyota",
        "modelo":           "GR Yaris Rally1",
        "anio":             2026,
        "tipo_combustible": "hibrido",
        "motor": {
            "hp":                520.0,
            "velocidad_punta_kmh": 215.0,
            "cilindrada_cc":     1600,
            "torque_nm":         440,
        },
        "configuracion": {
            "traccion":     "4WD",
            "transmision":  "secuencial 5 velocidades",
            "suspension":   "doble horquilla delantera / multilink trasera",
        },
        "estado_mecanico": {
            "ok":              True,
            "ultima_revision": fecha(2026, 7, 11),
        },
    },
    {
        "equipo_id":        "eq_andes",
        "marca":            "Toyota",
        "modelo":           "Corolla Rally2",
        "anio":             2026,
        "tipo_combustible": "nafta",
        "motor": {
            "hp":                480.0,
            "velocidad_punta_kmh": 208.0,
            "cilindrada_cc":     1600,
            "torque_nm":         410,
        },
        "configuracion": {
            "traccion":     "4WD",
            "transmision":  "secuencial 5 velocidades",
            "suspension":   "McPherson delantera / multilink trasera",
        },
        "estado_mecanico": {
            "ok":              True,
            "ultima_revision": fecha(2026, 7, 13),
        },
    },
    {
        "equipo_id":        "eq_samurai",
        "marca":            "Hyundai",
        "modelo":           "i20 N Rally1",
        "anio":             2026,
        "tipo_combustible": "hibrido",
        "motor": {
            "hp":                510.0,
            "velocidad_punta_kmh": 212.0,
            "cilindrada_cc":     1600,
            "torque_nm":         430,
        },
        "configuracion": {
            "traccion":     "4WD",
            "transmision":  "secuencial 5 velocidades",
            "suspension":   "MacPherson delantera / multilink trasera",
        },
        "estado_mecanico": {
            "ok":              True,
            "ultima_revision": fecha(2026, 7, 9),
        },
    },
    {
        "equipo_id":        "eq_samurai",
        "marca":            "Hyundai",
        "modelo":           "i20 Rally2",
        "anio":             2026,
        "tipo_combustible": "nafta",
        "motor": {
            "hp":                475.0,
            "velocidad_punta_kmh": 206.0,
            "cilindrada_cc":     1600,
            "torque_nm":         405,
        },
        "configuracion": {
            "traccion":     "4WD",
            "transmision":  "secuencial 5 velocidades",
            "suspension":   "MacPherson delantera / multilink trasera",
        },
        "estado_mecanico": {
            "ok":              True,
            "ultima_revision": fecha(2026, 7, 14),
        },
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  7. RALLIES
#  Neo4j: r1=Rally Finland → l1(Viernes)/l2(Sábado)/l3(Domingo)
#         l1→ss1,ss2,ss3 | l2→ss4,ss5,ss6 | l3→ss7,ss8(Power Stage)
#         ss1 tiene splits sp1, sp2, sp3
# ══════════════════════════════════════════════════════════════════════════════
rallies = [
    {
        "nombre":                   "Rally Finland",
        "temporada":                2026,
        "pais":                     "Finlandia",
        "sede":                     "Jyväskylä",
        "fecha_inicio":             fecha(2026, 7, 31),
        "fecha_fin":                fecha(2026, 8, 3),
        "superficie_principal":     "tierra",
        "equipos_participantes_ids": ["eq_monster", "eq_andes", "eq_samurai"],
        "legs": [
            {
                "nombre":     "Leg 1",
                "dia":        "Viernes",
                "special_stages": [
                    {
                        "nombre":          "SS1",
                        "kilometros":      12.5,
                        "superficie":      "tierra",
                        "splits": [
                            {"nombre": "Split 1", "km": 4.2,  "tiempo_objetivo": "00:02:08"},
                            {"nombre": "Split 2", "km": 8.1,  "tiempo_objetivo": "00:04:05"},
                            {"nombre": "Split 3", "km": 11.0, "tiempo_objetivo": "00:05:35"},
                        ],
                    },
                    {
                        "nombre":          "SS2",
                        "kilometros":      18.3,
                        "superficie":      "tierra",
                        "splits": [
                            {"nombre": "Split 1", "km": 6.0,  "tiempo_objetivo": "00:03:00"},
                            {"nombre": "Split 2", "km": 13.5, "tiempo_objetivo": "00:06:45"},
                        ],
                    },
                    {
                        "nombre":          "SS3",
                        "kilometros":      15.1,
                        "superficie":      "tierra",
                        "splits": [
                            {"nombre": "Split 1", "km": 5.5,  "tiempo_objetivo": "00:02:45"},
                            {"nombre": "Split 2", "km": 11.8, "tiempo_objetivo": "00:05:50"},
                        ],
                    },
                ],
            },
            {
                "nombre":     "Leg 2",
                "dia":        "Sábado",
                "special_stages": [
                    {
                        "nombre":     "SS4",
                        "kilometros": 21.4,
                        "superficie": "tierra",
                        "splits": [
                            {"nombre": "Split 1", "km": 7.0,  "tiempo_objetivo": "00:03:30"},
                            {"nombre": "Split 2", "km": 15.2, "tiempo_objetivo": "00:07:35"},
                        ],
                    },
                    {
                        "nombre":     "SS5",
                        "kilometros": 16.8,
                        "superficie": "tierra",
                        "splits": [
                            {"nombre": "Split 1", "km": 5.8,  "tiempo_objetivo": "00:02:55"},
                            {"nombre": "Split 2", "km": 12.4, "tiempo_objetivo": "00:06:10"},
                        ],
                    },
                    {
                        "nombre":     "SS6",
                        "kilometros": 19.2,
                        "superficie": "tierra",
                        "splits": [
                            {"nombre": "Split 1", "km": 6.5,  "tiempo_objetivo": "00:03:15"},
                            {"nombre": "Split 2", "km": 14.0, "tiempo_objetivo": "00:06:58"},
                        ],
                    },
                ],
            },
            {
                "nombre":     "Leg 3",
                "dia":        "Domingo",
                "special_stages": [
                    {
                        "nombre":     "SS7",
                        "kilometros": 14.7,
                        "superficie": "tierra",
                        "splits": [
                            {"nombre": "Split 1", "km": 5.0,  "tiempo_objetivo": "00:02:30"},
                            {"nombre": "Split 2", "km": 11.2, "tiempo_objetivo": "00:05:35"},
                        ],
                    },
                    {
                        "nombre":        "Power Stage",
                        "kilometros":    10.9,
                        "superficie":    "tierra",
                        "puntos_extra":  True,
                        "splits": [
                            {"nombre": "Split 1", "km": 4.0,  "tiempo_objetivo": "00:02:00"},
                            {"nombre": "Split 2", "km": 8.5,  "tiempo_objetivo": "00:04:15"},
                        ],
                    },
                ],
            },
        ],
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  8. RESUMENES DE CARRERA
# ══════════════════════════════════════════════════════════════════════════════
resumenes_carrera = [
    {
        "rally_id":         "rally_fin_2026",
        "titulo":           "Resumen Rally Finland 2026",
        "ganador":          "Luca Moretti",
        "fecha_generacion": fecha(2026, 8, 3),
        "podio": [
            {"piloto": "Luca Moretti",    "puesto": 1, "tiempo_total": "3:24:15.320"},
            {"piloto": "Carlos Benítez",  "puesto": 2, "tiempo_total": "3:24:48.711"},
            {"piloto": "Hiro Tanaka",     "puesto": 3, "tiempo_total": "3:25:10.004"},
        ],
        "abandons": [],
        "incidentes": [],
        "claves": ["victoria_moretti", "ritmo_constante", "estrategia", "power_stage"],
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  9. NOTICIAS Y REPORTES
# ══════════════════════════════════════════════════════════════════════════════
noticias_reportes = [
    {
        "rally_id": "rally_fin_2026",
        "tipo":     "analisis",
        "titular":  "Moretti administra el ritmo en SS4 y mantiene el liderato",
        "contenido": (
            "Durante el tramo SS4 del Leg 2 del Rally Finland 2026, el piloto Luca Moretti "
            "del equipo Monster Rally Team administró el ritmo de su Ford Puma Rally1. "
            "Con una estrategia conservadora, logró completar el tramo y conservar la primera posición."
        ),
        "fecha":    fecha(2026, 8, 1),
        "etiquetas": ["ritmo", "moretti", "ss4", "leg2"],
        "fuente":   "FIA Official Media",
    },
    {
        "rally_id": "rally_fin_2026",
        "tipo":     "analisis",
        "titular":  "Benítez ajusta la puesta a punto para el SS6",
        "contenido": (
            "El piloto Carlos Benítez de Andes Motorsport comunicó al equipo técnico "
            "cambios de puesta a punto en su Toyota GR Yaris Rally1 durante el SS6. "
            "El jefe de ingeniería Santiago Rivas confirmó que se revisarán los datos de telemetría "
            "antes del Leg 3."
        ),
        "fecha":    fecha(2026, 8, 2),
        "etiquetas": ["setup", "benitez", "ss6", "andes_motorsport"],
        "fuente":   "Andes Motorsport Official",
    },
    {
        "rally_id": "rally_fin_2026",
        "tipo":     "post_rally",
        "titular":  "Luca Moretti gana el Rally Finland 2026",
        "contenido": (
            "Luca Moretti del Monster Rally Team se impuso en el Rally Finland 2026 con un tiempo "
            "total de 3:24:15.320, seguido de cerca por Carlos Benítez (+33 seg) y Hiro Tanaka (+55 seg). "
            "Moretti suma su tercera victoria en la temporada y amplía su ventaja en el campeonato."
        ),
        "fecha":    fecha(2026, 8, 3),
        "etiquetas": ["victoria", "moretti", "fin_2026", "campeonato"],
        "fuente":   "FIA Official Media",
    },
    {
        "rally_id": "rally_fin_2026",
        "tipo":     "clima",
        "titular":  "Condiciones meteorológicas ideales esperadas para el Power Stage",
        "contenido": (
            "El servicio meteorológico de la FIA prevé condiciones de cielo despejado y temperatura "
            "de 18°C para el Power Stage del domingo, lo que favorece tiempos rápidos en la SS Power Stage "
            "del Rally Finland 2026."
        ),
        "fecha":    fecha(2026, 8, 2),
        "etiquetas": ["clima", "power_stage", "leg3", "condiciones"],
        "fuente":   "FIA Weather Service",
    },
    {
        "rally_id": "rally_fin_2026",
        "tipo":     "preview",
        "titular":  "Rally Finland 2026: Tres equipos y una lucha por el podio",
        "contenido": (
            "Con el inicio del Rally Finland a horas de comenzar, los tres equipos participantes "
            "–Monster Rally Team, Andes Motorsport y Samurai Racing– ultiman los detalles de sus "
            "configuraciones para los 8 tramos especiales que componen este exigente rally de tierra."
        ),
        "fecha":    fecha(2026, 7, 31),
        "etiquetas": ["preview", "rally_finland", "tres_equipos", "temporada_2026"],
        "fuente":   "WRC Media Office",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  INSERCIÓN EN MONGODB
# ══════════════════════════════════════════════════════════════════════════════
print("Cargando colecciones...")
print("-" * 45)

cargar_coleccion("patrocinador",      patrocinadores)
cargar_coleccion("jefe_ingenieria",   jefes_ingenieria)
cargar_coleccion("equipos",           equipos)
cargar_coleccion("copiloto",          copilotos)
cargar_coleccion("pilotos",           pilotos)
cargar_coleccion("vehiculos",         vehiculos)
cargar_coleccion("rallies",           rallies)
cargar_coleccion("resumenes_carrera", resumenes_carrera)
cargar_coleccion("noticias_reportes", noticias_reportes)

# ── Verificación final ────────────────────────────────────────────────────────
print("-" * 45)
print("\nVerificación de totales:")
colecciones = [
    "patrocinador", "jefe_ingenieria", "equipos", "copiloto",
    "pilotos", "vehiculos", "rallies", "resumenes_carrera", "noticias_reportes"
]
total = 0
for nombre in colecciones:
    count = db[nombre].count_documents({})
    print(f"  {nombre:<25} → {count} documentos")
    total += count

print(f"\n  {'TOTAL':<25} → {total} documentos")
print("\n✓  Dataset cargado correctamente en mundial_rally")
print("=" * 60)

print("\nMongoDB genero automaticamente los _id con ObjectId.")
print("=" * 60)

cliente.close()
