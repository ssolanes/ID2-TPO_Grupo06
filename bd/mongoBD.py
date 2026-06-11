# mongoBD.py
# Dataset completo de MongoDB para el proyecto WRC - TPO BDII 2026
#
# IMPORTANTE: Requiere MongoDB corriendo localmente en mongodb://localhost:27017/
# Instalación de dependencias: pip install pymongo
#
# Este dataset está sincronizado con neo4jBD.py:
#   - Los mismos 3 pilotos, copilotos, jefes de ingeniería, equipos, vehículos,
#     patrocinadores, rallies y fallas mecánicas están presentes en ambas BDs.
#   - Los _id de MongoDB coinciden con las propiedades usadas como clave en Neo4j.

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

# ─── Helper: limpiar e insertar colección ───────────────────────────────────
def cargar_coleccion(nombre: str, documentos: list):
    try:
        col = db[nombre]
        col.delete_many({})                    # limpiar datos anteriores
        resultado = col.insert_many(documentos)
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
        "_id":        "sponsor_redbull",
        "nombre":     "RedBull",
        "tipo":       "principal",
        "pais_origen":"Austria",
        "activo":     True,
    },
    {
        "_id":        "sponsor_pirelli",
        "nombre":     "Pirelli",
        "tipo":       "tecnico",
        "pais_origen":"Italia",
        "activo":     True,
    },
    {
        "_id":        "sponsor_shell",
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
        "_id":              "ji_ross",
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
        "_id":              "ji_rivas",
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
        "_id":              "ji_sato",
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
        "_id":                  "eq_monster",
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
        "_id":                  "eq_andes",
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
        "_id":                  "eq_samurai",
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
        "_id":               "copiloto_bellini",
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
        "_id":               "copiloto_suarez",
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
        "_id":               "copiloto_nakamura",
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
        "_id":              "piloto_moretti",
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
        "_id":              "piloto_benitez",
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
        "_id":              "piloto_tanaka",
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
#  Fallas: v1→f1(Motor/Alta), v3→f2(Suspensión/Media), v5→f3(Frenos/Alta)
# ══════════════════════════════════════════════════════════════════════════════
vehiculos = [
    {
        "_id":              "veh_puma_r1",
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
            "ok":              False,
            "ultima_revision": fecha(2026, 7, 10),
            "falla_activa":    {"tipo": "Motor", "gravedad": "Alta"},
        },
    },
    {
        "_id":              "veh_fiesta_r2",
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
            "falla_activa":    None,
        },
    },
    {
        "_id":              "veh_yaris_r1",
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
            "ok":              False,
            "ultima_revision": fecha(2026, 7, 11),
            "falla_activa":    {"tipo": "Suspensión", "gravedad": "Media"},
        },
    },
    {
        "_id":              "veh_corolla_r2",
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
            "falla_activa":    None,
        },
    },
    {
        "_id":              "veh_i20_r1",
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
            "ok":              False,
            "ultima_revision": fecha(2026, 7, 9),
            "falla_activa":    {"tipo": "Frenos", "gravedad": "Alta"},
        },
    },
    {
        "_id":              "veh_i20_r2",
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
            "falla_activa":    None,
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
        "_id":                      "rally_fin_2026",
        "nombre":                   "Rally Finland",
        "temporada":                2026,
        "campeonato":               "wrc_2026",
        "pais":                     "Finlandia",
        "sede":                     "Jyväskylä",
        "fecha_inicio":             fecha(2026, 7, 31),
        "fecha_fin":                fecha(2026, 8, 3),
        "superficie_principal":     "tierra",
        "equipos_participantes_ids": ["eq_monster", "eq_andes", "eq_samurai"],
        "legs": [
            {
                "leg_id":     "rally_fin_2026_l1",
                "nombre":     "Leg 1",
                "dia":        "Viernes",
                "special_stages": [
                    {
                        "ss_id":           "rally_fin_2026_ss1",
                        "nombre":          "SS1",
                        "kilometros":      12.5,
                        "superficie":      "tierra",
                        "splits": [
                            {"split_id": "rally_fin_2026_ss1_sp1", "nombre": "Split 1", "km": 4.2,  "tiempo_objetivo": "00:02:08"},
                            {"split_id": "rally_fin_2026_ss1_sp2", "nombre": "Split 2", "km": 8.1,  "tiempo_objetivo": "00:04:05"},
                            {"split_id": "rally_fin_2026_ss1_sp3", "nombre": "Split 3", "km": 11.0, "tiempo_objetivo": "00:05:35"},
                        ],
                    },
                    {
                        "ss_id":           "rally_fin_2026_ss2",
                        "nombre":          "SS2",
                        "kilometros":      18.3,
                        "superficie":      "tierra",
                        "splits": [
                            {"split_id": "rally_fin_2026_ss2_sp1", "nombre": "Split 1", "km": 6.0,  "tiempo_objetivo": "00:03:00"},
                            {"split_id": "rally_fin_2026_ss2_sp2", "nombre": "Split 2", "km": 13.5, "tiempo_objetivo": "00:06:45"},
                        ],
                    },
                    {
                        "ss_id":           "rally_fin_2026_ss3",
                        "nombre":          "SS3",
                        "kilometros":      15.1,
                        "superficie":      "tierra",
                        "splits": [
                            {"split_id": "rally_fin_2026_ss3_sp1", "nombre": "Split 1", "km": 5.5,  "tiempo_objetivo": "00:02:45"},
                            {"split_id": "rally_fin_2026_ss3_sp2", "nombre": "Split 2", "km": 11.8, "tiempo_objetivo": "00:05:50"},
                        ],
                    },
                ],
            },
            {
                "leg_id":     "rally_fin_2026_l2",
                "nombre":     "Leg 2",
                "dia":        "Sábado",
                "special_stages": [
                    {
                        "ss_id":      "rally_fin_2026_ss4",
                        "nombre":     "SS4",
                        "kilometros": 21.4,
                        "superficie": "tierra",
                        "splits": [
                            {"split_id": "rally_fin_2026_ss4_sp1", "nombre": "Split 1", "km": 7.0,  "tiempo_objetivo": "00:03:30"},
                            {"split_id": "rally_fin_2026_ss4_sp2", "nombre": "Split 2", "km": 15.2, "tiempo_objetivo": "00:07:35"},
                        ],
                    },
                    {
                        "ss_id":      "rally_fin_2026_ss5",
                        "nombre":     "SS5",
                        "kilometros": 16.8,
                        "superficie": "tierra",
                        "splits": [
                            {"split_id": "rally_fin_2026_ss5_sp1", "nombre": "Split 1", "km": 5.8,  "tiempo_objetivo": "00:02:55"},
                            {"split_id": "rally_fin_2026_ss5_sp2", "nombre": "Split 2", "km": 12.4, "tiempo_objetivo": "00:06:10"},
                        ],
                    },
                    {
                        "ss_id":      "rally_fin_2026_ss6",
                        "nombre":     "SS6",
                        "kilometros": 19.2,
                        "superficie": "tierra",
                        "splits": [
                            {"split_id": "rally_fin_2026_ss6_sp1", "nombre": "Split 1", "km": 6.5,  "tiempo_objetivo": "00:03:15"},
                            {"split_id": "rally_fin_2026_ss6_sp2", "nombre": "Split 2", "km": 14.0, "tiempo_objetivo": "00:06:58"},
                        ],
                    },
                ],
            },
            {
                "leg_id":     "rally_fin_2026_l3",
                "nombre":     "Leg 3",
                "dia":        "Domingo",
                "special_stages": [
                    {
                        "ss_id":      "rally_fin_2026_ss7",
                        "nombre":     "SS7",
                        "kilometros": 14.7,
                        "superficie": "tierra",
                        "splits": [
                            {"split_id": "rally_fin_2026_ss7_sp1", "nombre": "Split 1", "km": 5.0,  "tiempo_objetivo": "00:02:30"},
                            {"split_id": "rally_fin_2026_ss7_sp2", "nombre": "Split 2", "km": 11.2, "tiempo_objetivo": "00:05:35"},
                        ],
                    },
                    {
                        "ss_id":         "rally_fin_2026_ss8",
                        "nombre":        "Power Stage",
                        "kilometros":    10.9,
                        "superficie":    "tierra",
                        "puntos_extra":  True,
                        "splits": [
                            {"split_id": "rally_fin_2026_ss8_sp1", "nombre": "Split 1", "km": 4.0,  "tiempo_objetivo": "00:02:00"},
                            {"split_id": "rally_fin_2026_ss8_sp2", "nombre": "Split 2", "km": 8.5,  "tiempo_objetivo": "00:04:15"},
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
        "_id":              "resumen_fin_2026",
        "rally_id":         "rally_fin_2026",
        "fecha_generacion": fecha(2026, 8, 3),
        "podio": [
            {"pilot_id": "piloto_moretti",  "puesto": 1, "tiempo_total": "3:24:15.320"},
            {"pilot_id": "piloto_benitez",  "puesto": 2, "tiempo_total": "3:24:48.711"},
            {"pilot_id": "piloto_tanaka",   "puesto": 3, "tiempo_total": "3:25:10.004"},
        ],
        "abandons": [],
        "incidentes": [
            {
                "specialstage_id": "rally_fin_2026_ss4",
                "tipo":            "falla_mecanica",
                "descripcion":     "Moretti (veh_puma_r1) sufrió falla de motor en el SS4 pero logró completar el tramo.",
            },
            {
                "specialstage_id": "rally_fin_2026_ss6",
                "tipo":            "falla_mecanica",
                "descripcion":     "Benítez (veh_yaris_r1) reportó problemas de suspensión en el SS6.",
            },
        ],
        "claves": ["victoria_moretti", "falla_motor", "suspensión", "power_stage"],
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  9. NOTICIAS Y REPORTES
# ══════════════════════════════════════════════════════════════════════════════
noticias_reportes = [
    {
        "_id":      "noticia_fin_2026_001",
        "rally_id": "rally_fin_2026",
        "tipo":     "incidente",
        "titular":  "Moretti sufre falla de motor en SS4 pero mantiene el liderato",
        "contenido": (
            "Durante el tramo SS4 del Leg 2 del Rally Finland 2026, el piloto Luca Moretti "
            "del equipo Monster Rally Team reportó una falla de motor en su Ford Puma Rally1. "
            "A pesar del incidente, Moretti logró completar el tramo y conservar la primera posición."
        ),
        "fecha":    fecha(2026, 8, 1),
        "etiquetas": ["falla_motor", "moretti", "ss4", "leg2"],
        "fuente":   "FIA Official Media",
    },
    {
        "_id":      "noticia_fin_2026_002",
        "rally_id": "rally_fin_2026",
        "tipo":     "incidente",
        "titular":  "Benítez reporta problemas de suspensión en SS6",
        "contenido": (
            "El piloto Carlos Benítez de Andes Motorsport comunicó al equipo técnico "
            "problemas en la suspensión de su Toyota GR Yaris Rally1 durante el SS6. "
            "El jefe de ingeniería Santiago Rivas confirmó que se realizará una revisión completa "
            "antes del Leg 3."
        ),
        "fecha":    fecha(2026, 8, 2),
        "etiquetas": ["suspensión", "benitez", "ss6", "andes_motorsport"],
        "fuente":   "Andes Motorsport Official",
    },
    {
        "_id":      "noticia_fin_2026_003",
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
        "_id":      "noticia_fin_2026_004",
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
        "_id":      "noticia_fin_2026_005",
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

# ── Tabla de coherencia con Neo4j ────────────────────────────────────────────
print("\nCoherencia con neo4jBD.py:")
print("  Neo4j Nodo            MongoDB _id")
print("  " + "-" * 45)
tabla_coherencia = [
    ("Piloto: Luca Moretti",    "piloto_moretti"),
    ("Piloto: Carlos Benítez",  "piloto_benitez"),
    ("Piloto: Hiro Tanaka",     "piloto_tanaka"),
    ("Copiloto: Marco Bellini", "copiloto_bellini"),
    ("Copiloto: Diego Suárez",  "copiloto_suarez"),
    ("Copiloto: Yuki Nakamura", "copiloto_nakamura"),
    ("Equipo: Monster Rally",   "eq_monster"),
    ("Equipo: Andes Motorsport","eq_andes"),
    ("Equipo: Samurai Racing",  "eq_samurai"),
    ("Vehículo: Ford Puma R1",  "veh_puma_r1"),
    ("Vehículo: Toyota Yaris",  "veh_yaris_r1"),
    ("Vehículo: Hyundai i20 R1","veh_i20_r1"),
    ("Patrocinador: RedBull",   "sponsor_redbull"),
    ("Patrocinador: Pirelli",   "sponsor_pirelli"),
    ("Patrocinador: Shell",     "sponsor_shell"),
    ("Rally: Rally Finland",    "rally_fin_2026"),
]
for neo4j_label, mongo_id in tabla_coherencia:
    print(f"  {neo4j_label:<25} ↔  {mongo_id}")

print("=" * 60)

cliente.close()
