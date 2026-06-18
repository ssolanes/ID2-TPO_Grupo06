"""Carga masiva deterministica para MongoDB y Neo4j.

Agrega 1.500 entidades de dominio sin eliminar el dataset existente. La carga es
idempotente: usa upsert/MERGE con identificadores prefijados por ``bulk_``.
"""

from datetime import datetime, timezone
import os

from neo4j import GraphDatabase
from pymongo import MongoClient, ReplaceOne


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "mundial_rally")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
BATCH_SIZE = 200


PAISES = [
    ("AR", "Argentina"),
    ("IT", "Italia"),
    ("JP", "Japon"),
    ("FI", "Finlandia"),
    ("FR", "Francia"),
    ("ES", "Espana"),
    ("DE", "Alemania"),
    ("GB", "Reino Unido"),
    ("SE", "Suecia"),
    ("PT", "Portugal"),
]
MARCAS = ["Ford", "Toyota", "Hyundai", "Skoda", "Citroen", "Peugeot"]
SUPERFICIES = ["tierra", "asfalto", "nieve"]


def por_lotes(elementos, tamano=BATCH_SIZE):
    for inicio in range(0, len(elementos), tamano):
        yield elementos[inicio : inicio + tamano]


def fecha(anio, mes, dia):
    return datetime(anio, mes, dia, tzinfo=timezone.utc)


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
    return {clave: valor for clave, valor in doc.items() if clave not in campos}


def generar_documentos():
    colecciones = {
        "equipos": [],
        "pilotos": [],
        "copiloto": [],
        "vehiculos": [],
        "patrocinador": [],
        "jefe_ingenieria": [],
        "rallies": [],
        "noticias_reportes": [],
        "resumenes_carrera": [],
    }

    for indice in range(1, 101):
        codigo, pais = PAISES[(indice - 1) % len(PAISES)]
        equipo_id = f"bulk_equipo_{indice:04d}"
        rally_id = f"bulk_rally_{indice:04d}"
        sponsor_id = f"bulk_sponsor_{indice:04d}"
        jefe_id = f"bulk_jefe_{indice:04d}"
        vehiculos_ids = [f"bulk_vehiculo_{(indice - 1) * 3 + n:04d}" for n in range(1, 4)]
        pilotos_ids = [f"bulk_piloto_{(indice - 1) * 3 + n:04d}" for n in range(1, 4)]
        copilotos_ids = [f"bulk_copiloto_{(indice - 1) * 3 + n:04d}" for n in range(1, 4)]

        colecciones["equipos"].append(
            {
                "_id": equipo_id,
                "nombre": f"Equipo Rally {indice:03d}",
                "pais_base": pais,
                "director": f"Director {indice:03d}",
                "jefe_ingenieria_id": jefe_id,
                "pilotos_ids": pilotos_ids,
                "copilotos_ids": copilotos_ids,
                "vehiculos_ids": vehiculos_ids,
                "patrocinadores_ids": [sponsor_id],
                "activo": True,
                "origen_carga": "masiva_1500",
            }
        )
        colecciones["patrocinador"].append(
            {
                "_id": sponsor_id,
                "nombre": f"Patrocinador {indice:03d}",
                "tipo": ["principal", "tecnico", "logistico"][indice % 3],
                "pais_origen": pais,
                "activo": True,
                "origen_carga": "masiva_1500",
            }
        )
        colecciones["jefe_ingenieria"].append(
            {
                "_id": jefe_id,
                "nombre": f"Jefe{indice:03d}",
                "apellido": f"Ingenieria{indice:03d}",
                "especialidad": ["Motores", "Suspension", "Aerodinamica"][indice % 3],
                "equipo_id": equipo_id,
                "años_experiencia": 5 + indice % 21,
                "email": f"jefe{indice:03d}@wrc.test",
                "telefono": f"+54-11-5555-{indice:04d}",
                "certificaciones": ["FIA Motorsport Engineering"],
                "estado": "activo",
                "origen_carga": "masiva_1500",
            }
        )

        legs = []
        for leg_numero in range(1, 4):
            stages = []
            for stage_numero in range(1, 3):
                numero_ss = (leg_numero - 1) * 2 + stage_numero
                stages.append(
                    {
                        "ss_id": f"{rally_id}_ss{numero_ss}",
                        "nombre": f"SS{numero_ss}",
                        "kilometros": round(10 + indice % 12 + numero_ss * 0.7, 1),
                        "superficie": SUPERFICIES[(indice + numero_ss) % 3],
                        "splits": [
                            {
                                "split_id": f"{rally_id}_ss{numero_ss}_sp{split}",
                                "nombre": f"Split {split}",
                                "km": round((4.0 + split * 2.5), 1),
                                "tiempo_objetivo": f"00:0{split}:{20 + indice % 35:02d}",
                            }
                            for split in range(1, 3)
                        ],
                    }
                )
            legs.append(
                {
                    "leg_id": f"{rally_id}_l{leg_numero}",
                    "nombre": f"Leg {leg_numero}",
                    "dia": ["Viernes", "Sabado", "Domingo"][leg_numero - 1],
                    "special_stages": stages,
                }
            )

        colecciones["rallies"].append(
            {
                "_id": rally_id,
                "nombre": f"Rally Internacional {indice:03d}",
                "temporada": 2026,
                "campeonato": "wrc_2026",
                "pais": pais,
                "sede": f"Sede {indice:03d}",
                "fecha_inicio": fecha(2026, (indice - 1) % 12 + 1, 1),
                "fecha_fin": fecha(2026, (indice - 1) % 12 + 1, 3),
                "superficie_principal": SUPERFICIES[indice % 3],
                "equipos_participantes_ids": [equipo_id],
                "legs": legs,
                "origen_carga": "masiva_1500",
            }
        )

        colecciones["noticias_reportes"].append(
            {
                "_id": f"bulk_noticia_{indice:04d}",
                "rally_id": rally_id,
                "tipo": ["previa", "resultado", "incidente"][indice % 3],
                "titular": f"Reporte oficial del Rally {indice:03d}",
                "contenido": f"Informe generado para la carga masiva del rally {indice:03d}.",
                "fecha": fecha(2026, (indice - 1) % 12 + 1, 4),
                "etiquetas": ["wrc", "carga_masiva", codigo.lower()],
                "fuente": "WRC Data Lab",
                "origen_carga": "masiva_1500",
            }
        )
        colecciones["resumenes_carrera"].append(
            {
                "_id": f"bulk_resumen_{indice:04d}",
                "rally_id": rally_id,
                "titulo": f"Resumen Rally {indice:03d}",
                "fecha_generacion": fecha(2026, (indice - 1) % 12 + 1, 4),
                "ganador": f'Piloto{(indice - 1) * 3 + 1:04d} WRC{(indice - 1) * 3 + 1:04d}',
                "podio": [
                    {
                        "piloto": f'Piloto{((indice - 1) * 3 + puesto):04d} WRC{((indice - 1) * 3 + puesto):04d}',
                        "puesto": puesto,
                        "tiempo_total": f"03:{20 + puesto:02d}:{indice % 60:02d}.000",
                    }
                    for puesto in range(1, 4)
                ],
                "abandons": [],
                "incidentes": [],
                "claves": ["carga_masiva", "temporada_2026"],
                "origen_carga": "masiva_1500",
            }
        )

        for posicion in range(3):
            numero = (indice - 1) * 3 + posicion + 1
            piloto_id = pilotos_ids[posicion]
            copiloto_id = copilotos_ids[posicion]
            vehiculo_id = vehiculos_ids[posicion]
            marca = MARCAS[(numero - 1) % len(MARCAS)]

            colecciones["pilotos"].append(
                {
                    "_id": piloto_id,
                    "nombre": f"Piloto{numero:04d}",
                    "apellido": f"WRC{numero:04d}",
                    "fecha_nacimiento": fecha(1985 + numero % 16, numero % 12 + 1, numero % 27 + 1),
                    "pais": {"codigo": codigo, "nombre": pais},
                    "equipo_id": equipo_id,
                    "copiloto_id": copiloto_id,
                    "vehiculo_id": vehiculo_id,
                    "numero_auto": 1000 + numero,
                    "estado": "activo",
                    "sponsors": [sponsor_id],
                    "estadisticas": {
                        "puntos": numero % 180,
                        "victorias": numero % 8,
                        "podios": numero % 15,
                        "rallies_disputados": 5 + numero % 40,
                    },
                    "origen_carga": "masiva_1500",
                }
            )
            colecciones["copiloto"].append(
                {
                    "_id": copiloto_id,
                    "nombre": f"Copiloto{numero:04d}",
                    "apellido": f"WRC{numero:04d}",
                    "fecha_nacimiento": fecha(1984 + numero % 17, numero % 12 + 1, numero % 27 + 1),
                    "pais": {"codigo": codigo, "nombre": pais},
                    "equipo_id": equipo_id,
                    "piloto_id": piloto_id,
                    "años_experiencia": 2 + numero % 20,
                    "idiomas": ["espanol", "ingles"],
                    "estado": "activo",
                    "origen_carga": "masiva_1500",
                }
            )
            colecciones["vehiculos"].append(
                {
                    "_id": vehiculo_id,
                    "equipo_id": equipo_id,
                    "marca": marca,
                    "modelo": f"Rally {numero:04d}",
                    "anio": 2026,
                    "tipo_combustible": "hibrido",
                    "motor": {
                        "hp": float(430 + numero % 91),
                        "velocidad_punta_kmh": float(195 + numero % 26),
                        "cilindrada_cc": 1600,
                        "torque_nm": 390 + numero % 61,
                    },
                    "configuracion": {
                        "traccion": "4WD",
                        "transmision": "secuencial 5 velocidades",
                        "suspension": "competicion regulable",
                    },
                    "estado_mecanico": {
                        "ok": numero % 10 != 0,
                        "ultima_revision": fecha(2026, 1, numero % 27 + 1),
                        "falla_activa": None if numero % 10 else {"tipo": "Suspension", "gravedad": "Media"},
                    },
                    "origen_carga": "masiva_1500",
                }
            )

    total = sum(len(documentos) for documentos in colecciones.values())
    if total != 1500:
        raise RuntimeError(f"La generacion produjo {total} documentos en vez de 1500")
    return colecciones


def cargar_mongodb(db, colecciones):
    for nombre, documentos in colecciones.items():
        operaciones = [
            ReplaceOne({"_id": doc["_id"]}, doc_mongo_limpio(nombre, doc), upsert=True)
            for doc in documentos
        ]
        resultado = db[nombre].bulk_write(operaciones, ordered=False)
        print(
            f"MongoDB {nombre:<22} total={len(documentos):>3} "
            f"insertados={resultado.upserted_count:>3} modificados={resultado.modified_count:>3}"
        )


def filas_neo4j(colecciones):
    return {
        "Equipo": [
            {"mongo_id": d["_id"], "props": {"nombre": d["nombre"], "pais": d["pais_base"], "director": d["director"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["equipos"]
        ],
        "Piloto": [
            {"mongo_id": d["_id"], "props": {"nombre": f'{d["nombre"]} {d["apellido"]}', "pais": d["pais"]["nombre"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["pilotos"]
        ],
        "Copiloto": [
            {"mongo_id": d["_id"], "props": {"nombre": f'{d["nombre"]} {d["apellido"]}', "pais": d["pais"]["nombre"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["copiloto"]
        ],
        "Vehiculo": [
            {"mongo_id": d["_id"], "props": {"modelo": f'{d["marca"]} {d["modelo"]}', "marca": d["marca"], "anio": d["anio"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["vehiculos"]
        ],
        "Patrocinador": [
            {"mongo_id": d["_id"], "props": {"nombre": d["nombre"], "industria": d["tipo"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["patrocinador"]
        ],
        "JefeIngenieria": [
            {"mongo_id": d["_id"], "props": {"nombre": f'{d["nombre"]} {d["apellido"]}', "especialidad": d["especialidad"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["jefe_ingenieria"]
        ],
        "Rally": [
            {"mongo_id": d["_id"], "props": {"nombre": d["nombre"], "pais": d["pais"], "temporada": d["temporada"], "superficie": d["superficie_principal"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["rallies"]
        ],
        "NoticiaReporte": [
            {"mongo_id": d["_id"], "props": {"titular": d["titular"], "tipo": d["tipo"], "fuente": d["fuente"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["noticias_reportes"]
        ],
        "ResumenCarrera": [
            {"mongo_id": d["_id"], "props": {"titulo": d["titulo"], "ganador": d["ganador"], "origen_carga": d["origen_carga"]}}
            for d in colecciones["resumenes_carrera"]
        ],
    }


def ejecutar_escritura(driver, consulta, filas):
    for lote in por_lotes(filas):
        driver.execute_query(consulta, rows=lote, database_="neo4j")


def cargar_neo4j(driver, colecciones):
    nodos = filas_neo4j(colecciones)
    for label, filas in nodos.items():
        consulta = f"""
        UNWIND $rows AS row
        MERGE (n:{label} {{mongo_id: row.mongo_id}})
        SET n += row.props
        """
        ejecutar_escritura(driver, consulta, filas)
        print(f"Neo4j   {label:<22} nodos={len(filas):>3}")

    relaciones = {
        ("Piloto", "PERTENECE_A", "Equipo"): [
            {"origen": d["_id"], "destino": d["equipo_id"]} for d in colecciones["pilotos"]
        ],
        ("Piloto", "CONDUCE", "Vehiculo"): [
            {"origen": d["_id"], "destino": d["vehiculo_id"]} for d in colecciones["pilotos"]
        ],
        ("Piloto", "TIENE_COPILOTO", "Copiloto"): [
            {"origen": d["_id"], "destino": d["copiloto_id"]} for d in colecciones["pilotos"]
        ],
        ("Piloto", "PARTICIPA_EN", "Rally"): [
            {"origen": d["_id"], "destino": f'bulk_rally_{int(d["_id"].split("_")[-1]):04d}'}
            for d in colecciones["pilotos"]
        ],
        ("Copiloto", "PERTENECE_A", "Equipo"): [
            {"origen": d["_id"], "destino": d["equipo_id"]} for d in colecciones["copiloto"]
        ],
        ("Copiloto", "ASISTE_EN", "Vehiculo"): [
            {"origen": d["_id"], "destino": f'bulk_vehiculo_{int(d["_id"].split("_")[-1]):04d}'}
            for d in colecciones["copiloto"]
        ],
        ("Copiloto", "PARTICIPA_EN", "Rally"): [
            {"origen": d["_id"], "destino": f'bulk_rally_{int(d["_id"].split("_")[-1]):04d}'}
            for d in colecciones["copiloto"]
        ],
        ("Equipo", "USA", "Vehiculo"): [
            {"origen": d["equipo_id"], "destino": d["_id"]} for d in colecciones["vehiculos"]
        ],
        ("Equipo", "PARTICIPA_EN", "Rally"): [
            {"origen": d["_id"], "destino": f'bulk_rally_{int(d["_id"].split("_")[-1]):04d}'}
            for d in colecciones["equipos"]
        ],
        ("Patrocinador", "PATROCINA", "Equipo"): [
            {"origen": d["_id"], "destino": f'bulk_equipo_{int(d["_id"].split("_")[-1]):04d}'}
            for d in colecciones["patrocinador"]
        ],
        ("JefeIngenieria", "DIRIGE", "Equipo"): [
            {"origen": d["_id"], "destino": d["equipo_id"]} for d in colecciones["jefe_ingenieria"]
        ],
        ("NoticiaReporte", "HABLA_DE", "Rally"): [
            {"origen": d["_id"], "destino": d["rally_id"]} for d in colecciones["noticias_reportes"]
        ],
        ("ResumenCarrera", "RESUME", "Rally"): [
            {"origen": d["_id"], "destino": d["rally_id"]} for d in colecciones["resumenes_carrera"]
        ],
    }

    total_relaciones = 0
    for (origen_label, tipo, destino_label), filas in relaciones.items():
        consulta = f"""
        UNWIND $rows AS row
        MATCH (a:{origen_label} {{mongo_id: row.origen}})
        MATCH (b:{destino_label} {{mongo_id: row.destino}})
        MERGE (a)-[:{tipo}]->(b)
        """
        ejecutar_escritura(driver, consulta, filas)
        total_relaciones += len(filas)
    print(f"Neo4j   relaciones masivas    total={total_relaciones}")


def verificar(db, driver):
    mongo_total = sum(
        db[nombre].count_documents({"origen_carga": "masiva_1500"})
        for nombre in (
            "equipos", "pilotos", "copiloto", "vehiculos", "patrocinador",
            "jefe_ingenieria", "rallies", "noticias_reportes", "resumenes_carrera",
        )
    )
    registros, _, _ = driver.execute_query(
        "MATCH (n {origen_carga: 'masiva_1500'}) RETURN count(n) AS total",
        database_="neo4j",
    )
    neo_total = registros[0]["total"]
    relaciones, _, _ = driver.execute_query(
        "MATCH (a {origen_carga: 'masiva_1500'})-[r]->(b {origen_carga: 'masiva_1500'}) RETURN count(r) AS total",
        database_="neo4j",
    )
    rel_total = relaciones[0]["total"]
    print("\nVerificacion final")
    print(f"MongoDB documentos masivos: {mongo_total}")
    print(f"Neo4j nodos masivos:        {neo_total}")
    print(f"Neo4j relaciones masivas:   {rel_total}")
    if mongo_total != 1500 or neo_total != 1500:
        raise RuntimeError("La carga no alcanzo los 1.500 documentos/nodos esperados")


def main():
    colecciones = generar_documentos()
    cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    cliente.admin.command("ping")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    try:
        cargar_mongodb(cliente[MONGO_DB], colecciones)
        cargar_neo4j(driver, colecciones)
        verificar(cliente[MONGO_DB], driver)
    finally:
        driver.close()
        cliente.close()


if __name__ == "__main__":
    main()
