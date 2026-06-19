"""Carga masiva limpia para MongoDB y Neo4j.

Reglas principales:
- MongoDB genera todos los _id automaticamente.
- MongoDB guarda documentos completos, sin estructuras de grafo ni campos de
  control de la carga dentro de las entidades.
- Neo4j guarda nodos livianos con mongo_id = str(_id de MongoDB).
- Las relaciones de Neo4j se crean buscando nodos por mongo_id.

La carga se puede ejecutar varias veces. Para reemplazar los datos masivos
anteriores se guardan los _id insertados en una coleccion tecnica de metadata,
no en los documentos de negocio.
"""

from datetime import datetime, timezone
import os
import sys

from bson import ObjectId
from neo4j import GraphDatabase
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "mundial_rally")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")

LIMPIAR_ANTES_DE_CARGAR = False
BATCH_SIZE = 250
CARGA_ID = "world_rally_bulk"
METADATA_COLLECTION = "_carga_masiva_meta"
LEGACY_ORIGEN_CARGA = "carga_masiva_world_rally"


MONGO_COLLECTIONS = (
    "campeonatos",
    "equipos",
    "pilotos",
    "copiloto",
    "jefe_ingenieria",
    "vehiculos",
    "rallies",
    "patrocinador",
    "resumenes_carrera",
    "noticias_reportes",
)

LEGACY_COLLECTIONS = MONGO_COLLECTIONS + ("fallas_mecanicas",)

NEO_LABELS = {
    "campeonatos": "Campeonato",
    "equipos": "Equipo",
    "pilotos": "Piloto",
    "copiloto": "Copiloto",
    "jefe_ingenieria": "JefeIngenieria",
    "vehiculos": "Vehiculo",
    "rallies": "Rally",
    "patrocinador": "Patrocinador",
    "resumenes_carrera": "ResumenCarrera",
    "noticias_reportes": "NoticiaReporte",
}

RELACIONES_NEO_PERMITIDAS = {
    ("Campeonato", "TIENE_RALLY", "Rally"),
    ("Piloto", "PERTENECE_A", "Equipo"),
    ("Piloto", "CONDUCE", "Vehiculo"),
    ("Piloto", "PARTICIPA_EN", "Rally"),
    ("Copiloto", "PERTENECE_A", "Equipo"),
    ("Copiloto", "ASISTE_EN", "Vehiculo"),
    ("Copiloto", "PARTICIPA_EN", "Rally"),
    ("Equipo", "USA", "Vehiculo"),
    ("Equipo", "PARTICIPA_EN", "Rally"),
    ("Patrocinador", "PATROCINA", "Equipo"),
    ("JefeIngenieria", "DIRIGE", "Equipo"),
    ("ResumenCarrera", "RESUME", "Rally"),
}

COUNTS = {
    "campeonatos": 1,
    "equipos": 40,
    "pilotos": 160,
    "copiloto": 160,
    "jefe_ingenieria": 80,
    "vehiculos": 180,
    "rallies": 120,
    "patrocinador": 120,
    "resumenes_carrera": 200,
    "noticias_reportes": 439,
}

PAISES = [
    ("AR", "Argentina"),
    ("CL", "Chile"),
    ("UY", "Uruguay"),
    ("BR", "Brasil"),
    ("IT", "Italia"),
    ("FI", "Finlandia"),
    ("SE", "Suecia"),
    ("FR", "Francia"),
    ("ES", "Espana"),
    ("JP", "Japon"),
]
MARCAS = ["Ford", "Toyota", "Hyundai", "Skoda", "Citroen", "Peugeot"]
SUPERFICIES = ["tierra", "asfalto", "nieve", "mixta"]
ESPECIALIDADES = ["Motores", "Suspension", "Aerodinamica", "Telemetria"]


def fecha(anio, mes, dia):
    return datetime(anio, mes, dia, tzinfo=timezone.utc)


def por_lotes(items, size=BATCH_SIZE):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def conectar_mongo():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print(f"MongoDB conectado: {MONGO_URI} / {MONGO_DB}")
        return client
    except ServerSelectionTimeoutError as exc:
        raise RuntimeError(f"No se pudo conectar a MongoDB: {exc}") from exc


def conectar_neo4j():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print(f"Neo4j conectado: {NEO4J_URI}")
        return driver
    except Exception as exc:
        raise RuntimeError(f"No se pudo conectar a Neo4j: {exc}") from exc


def pais(idx):
    codigo, nombre = PAISES[idx % len(PAISES)]
    return {"codigo": codigo, "nombre": nombre}


def nombre_persona(prefijo, idx):
    return f"{prefijo}{idx:03d}", f"Rally{idx:03d}"


def agregar(collections, collection_name, tmp_key, doc):
    doc["__tmp_key"] = tmp_key
    collections[collection_name].append(doc)


def generar_datos():
    data = {name: [] for name in MONGO_COLLECTIONS}

    for i in range(COUNTS["campeonatos"]):
        agregar(
            data,
            "campeonatos",
            f"campeonato:{i}",
            {
                "nombre": f"World Rally Championship {2024 + i}",
                "temporada": 2024 + i,
                "categoria": "WRC",
                "organizador": "FIA World Rally",
            },
        )

    for i in range(COUNTS["equipos"]):
        country = pais(i)
        agregar(
            data,
            "equipos",
            f"equipo:{i}",
            {
                "nombre": f"{MARCAS[i % len(MARCAS)]} Rally Team {i + 1:02d}",
                "pais_base": country["nombre"],
                "director": f"Director Tecnico {i + 1:02d}",
            },
        )

    for i in range(COUNTS["jefe_ingenieria"]):
        nombre, apellido = nombre_persona("Jefe", i + 1)
        especialidad = ESPECIALIDADES[i % len(ESPECIALIDADES)]
        agregar(
            data,
            "jefe_ingenieria",
            f"jefe:{i}",
            {
                "__equipo_key": f"equipo:{i % COUNTS['equipos']}",
                "nombre": nombre,
                "apellido": apellido,
                "especialidad": especialidad,
                "email": f"jefe{i + 1:03d}@wrc.test",
                "telefono": f"+54-11-6000-{i + 1:04d}",
                "certificaciones": [
                    "FIA Motorsport Engineering",
                    f"{especialidad} WRC Specialist",
                ],
            },
        )

    for i in range(COUNTS["vehiculos"]):
        marca = MARCAS[i % len(MARCAS)]
        agregar(
            data,
            "vehiculos",
            f"vehiculo:{i}",
            {
                "__equipo_key": f"equipo:{i % COUNTS['equipos']}",
                "marca": marca,
                "modelo": f"{marca} Rally {1 + (i % 5)}",
                "anio": 2021 + (i % 6),
                "tipo_combustible": "hibrido" if i % 3 == 0 else "nafta",
                "configuracion": {"traccion": "4WD"},
                "estado_mecanico": {
                    "ok": True,
                    "ultima_revision": fecha(2026, 1 + (i % 12), 1 + (i % 24)),
                },
            },
        )

    for i in range(COUNTS["pilotos"]):
        nombre, apellido = nombre_persona("Piloto", i + 1)
        agregar(
            data,
            "pilotos",
            f"piloto:{i}",
            {
                "__equipo_key": f"equipo:{i % COUNTS['equipos']}",
                "__copiloto_key": f"copiloto:{i}",
                "__vehiculo_key": f"vehiculo:{i % COUNTS['vehiculos']}",
                "nombre": nombre,
                "apellido": apellido,
                "pais": pais(i),
            },
        )

    for i in range(COUNTS["copiloto"]):
        nombre, apellido = nombre_persona("Copiloto", i + 1)
        agregar(
            data,
            "copiloto",
            f"copiloto:{i}",
            {
                "__equipo_key": f"equipo:{i % COUNTS['equipos']}",
                "__piloto_key": f"piloto:{i}",
                "__vehiculo_key": f"vehiculo:{i % COUNTS['vehiculos']}",
                "nombre": nombre,
                "apellido": apellido,
                "pais": pais(i + 3),
            },
        )

    for i in range(COUNTS["rallies"]):
        country = pais(i + 5)
        agregar(
            data,
            "rallies",
            f"rally:{i}",
            {
                "__campeonato_key": "campeonato:0",
                "__equipos_keys": [f"equipo:{(i + offset) % COUNTS['equipos']}" for offset in range(8)],
                "nombre": f"Rally {country['nombre']} {2024 + (i % 3)} #{i + 1:03d}",
                "temporada": 2024 + (i % 3),
                "pais": country["nombre"],
                "sede": f"Sede Rally {i + 1:03d}",
                "superficie_principal": SUPERFICIES[i % len(SUPERFICIES)],
                "fecha_inicio": fecha(2024 + (i % 3), 1 + (i % 12), 3),
                "fecha_fin": fecha(2024 + (i % 3), 1 + (i % 12), 5),
                "legs": generar_legs(i),
            },
        )

    for i in range(COUNTS["patrocinador"]):
        agregar(
            data,
            "patrocinador",
            f"patrocinador:{i}",
            {
                "__equipo_key": f"equipo:{i % COUNTS['equipos']}",
                "nombre": f"Patrocinador Global {i + 1:03d}",
                "tipo": ["principal", "tecnico", "logistico"][i % 3],
            },
        )

    for i in range(COUNTS["resumenes_carrera"]):
        piloto_idx = i % COUNTS["pilotos"]
        agregar(
            data,
            "resumenes_carrera",
            f"resumen:{i}",
            {
                "__rally_key": f"rally:{i % COUNTS['rallies']}",
                "titulo": f"Resumen de carrera {i + 1:03d}",
                "fecha_generacion": fecha(2026, 1 + (i % 12), 10),
                "ganador": f"Piloto{piloto_idx + 1:03d} Rally{piloto_idx + 1:03d}",
                "podio": [
                    {"puesto": 1, "piloto": f"Piloto{piloto_idx + 1:03d} Rally{piloto_idx + 1:03d}"},
                    {"puesto": 2, "piloto": f"Piloto{((piloto_idx + 1) % COUNTS['pilotos']) + 1:03d} Rally{((piloto_idx + 1) % COUNTS['pilotos']) + 1:03d}"},
                    {"puesto": 3, "piloto": f"Piloto{((piloto_idx + 2) % COUNTS['pilotos']) + 1:03d} Rally{((piloto_idx + 2) % COUNTS['pilotos']) + 1:03d}"},
                ],
                "claves": ["ritmo", "regularidad", "estrategia"],
            },
        )

    for i in range(COUNTS["noticias_reportes"]):
        agregar(
            data,
            "noticias_reportes",
            f"noticia:{i}",
            {
                "tipo": ["previa", "resultado", "analisis"][i % 3],
                "titular": f"Reporte WRC {i + 1:03d}",
                "contenido": f"Reporte generado para la carga masiva numero {i + 1}.",
                "fecha": fecha(2026, 1 + (i % 12), 12),
                "etiquetas": ["wrc", "datos", "carga_masiva"],
                "fuente": "WRC Data Lab",
            },
        )

    total = sum(len(items) for items in data.values())
    expected = sum(COUNTS.values())
    if total != expected:
        raise RuntimeError(f"Se generaron {total} documentos, se esperaban {expected}")
    return data


def generar_legs(seed):
    legs = []
    for leg in range(1, 4):
        stages = []
        for stage in range(1, 3):
            stages.append(
                {
                    "nombre": f"SS{((leg - 1) * 2) + stage}",
                    "kilometros": round(9.5 + ((seed + leg + stage) % 18), 1),
                    "superficie": SUPERFICIES[(seed + leg + stage) % len(SUPERFICIES)],
                    "splits": [
                        {"nombre": "Split 1", "km": 4.5},
                        {"nombre": "Split 2", "km": 9.0},
                    ],
                }
            )
        legs.append({"nombre": f"Leg {leg}", "dia": f"Dia {leg}", "special_stages": stages})
    return legs


def limpiar_doc(doc):
    return {key: value for key, value in doc.items() if not key.startswith("__")}


def indexar_por_tmp_key(data):
    index = {}
    for docs in data.values():
        for doc in docs:
            tmp_key = doc["__tmp_key"]
            if tmp_key in index:
                raise RuntimeError(f"Clave temporal duplicada: {tmp_key}")
            index[tmp_key] = doc
    return index


def ref(index, tmp_key):
    if tmp_key not in index:
        raise RuntimeError(f"Referencia temporal inexistente: {tmp_key}")
    if "_id" not in index[tmp_key]:
        raise RuntimeError(f"Referencia usada antes de insertar en MongoDB: {tmp_key}")
    return index[tmp_key]["_id"]


def object_ids(ids):
    values = []
    for value in ids:
        try:
            values.append(ObjectId(value))
        except Exception:
            continue
    return values


def limpiar_datos_previos(db, driver):
    old_mongo_ids = set()

    driver.execute_query("MATCH ()-[r:HABLA_DE]->() DELETE r", database_="neo4j")
    driver.execute_query("MATCH ()-[r:TIENE_FALLA]->() DELETE r", database_="neo4j")
    driver.execute_query("MATCH (n:FallaMecanica) DETACH DELETE n", database_="neo4j")

    if LIMPIAR_ANTES_DE_CARGAR:
        print("Limpieza completa habilitada: se borran colecciones y labels de la carga.")
        for collection in LEGACY_COLLECTIONS:
            deleted = db[collection].delete_many({}).deleted_count
            print(f"MongoDB {collection:<20} borrados={deleted}")
        db[METADATA_COLLECTION].delete_one({"_id": CARGA_ID})
        driver.execute_query(
            """
            MATCH (n)
            WHERE any(label IN labels(n) WHERE label IN $labels)
            DETACH DELETE n
            """,
            labels=list(NEO_LABELS.values()),
            database_="neo4j",
        )
        return

    print("Limpieza segura: se reemplaza solo la carga masiva anterior.")
    metadata = db[METADATA_COLLECTION].find_one({"_id": CARGA_ID}) or {}
    for collection, ids in metadata.get("mongo_ids", {}).items():
        oid_values = object_ids(ids)
        if not oid_values:
            continue
        deleted = db[collection].delete_many({"_id": {"$in": oid_values}}).deleted_count
        old_mongo_ids.update(ids)
        print(f"MongoDB {collection:<20} borrados_metadata={deleted}")

    for collection in LEGACY_COLLECTIONS:
        legacy_ids = [
            str(doc["_id"])
            for doc in db[collection].find({"origen_carga": LEGACY_ORIGEN_CARGA}, {"_id": 1})
        ]
        if legacy_ids:
            deleted = db[collection].delete_many({"_id": {"$in": object_ids(legacy_ids)}}).deleted_count
            old_mongo_ids.update(legacy_ids)
            print(f"MongoDB {collection:<20} borrados_legacy={deleted}")

    db[METADATA_COLLECTION].delete_one({"_id": CARGA_ID})

    if old_mongo_ids:
        driver.execute_query(
            """
            MATCH (n)
            WHERE n.mongo_id IN $mongo_ids
            DETACH DELETE n
            """,
            mongo_ids=list(old_mongo_ids),
            database_="neo4j",
        )


def insertar_documentos(db, data):
    resumen = {}
    for collection, docs in data.items():
        payload = [limpiar_doc(doc) for doc in docs]
        if not payload:
            resumen[collection] = 0
            continue
        result = db[collection].insert_many(payload, ordered=True)
        for doc, inserted_id in zip(docs, result.inserted_ids):
            doc["_id"] = inserted_id
        resumen[collection] = len(result.inserted_ids)
        print(f"MongoDB {collection:<20} insertados={resumen[collection]}")
    return resumen


def guardar_metadata(db, data):
    mongo_ids = {
        collection: [str(doc["_id"]) for doc in docs]
        for collection, docs in data.items()
    }
    db[METADATA_COLLECTION].replace_one(
        {"_id": CARGA_ID},
        {
            "_id": CARGA_ID,
            "created_at": datetime.now(timezone.utc),
            "mongo_ids": mongo_ids,
        },
        upsert=True,
    )


def preparar_neo4j(driver):
    for label in NEO_LABELS.values():
        constraint_name = f"{label.lower()}_mongo_id_unique"
        driver.execute_query(
            f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.mongo_id IS UNIQUE
            """,
            database_="neo4j",
        )


def normalizar_nodos_neo4j(driver):
    driver.execute_query(
        """
        MATCH (n)
        WHERE n.mongo_id IS NOT NULL
        SET n = {
            mongo_id: n.mongo_id,
            nombre: coalesce(n.nombre, n.display_name, n.name, n.modelo, n.titular, n.titulo, n.mongo_id)
        }
        WITH n
        WHERE 'NoticiaReporte' IN labels(n)
        SET n += CASE
            WHEN 'NoticiaReporte' IN labels(n) THEN {titular: n.nombre}
            ELSE {}
        END
        """,
        database_="neo4j",
    )


def nombre_neo(collection, doc):
    if collection in ("pilotos", "copiloto", "jefe_ingenieria"):
        return f"{doc['nombre']} {doc['apellido']}"
    if collection == "vehiculos":
        return f"{doc['marca']} {doc['modelo']}"
    if collection == "noticias_reportes":
        return doc["titular"]
    if collection == "resumenes_carrera":
        return doc["titulo"]
    return doc["nombre"]


def props_neo(collection, doc):
    props = {
        "mongo_id": str(doc["_id"]),
        "nombre": nombre_neo(collection, doc),
    }
    if collection == "noticias_reportes":
        props["titular"] = props["nombre"]
    return props


def cargar_nodos_neo4j(driver, data):
    total = 0
    for collection, label in NEO_LABELS.items():
        docs = data[collection]
        rows = [{"mongo_id": str(doc["_id"]), "props": props_neo(collection, doc)} for doc in docs]
        for batch in por_lotes(rows):
            driver.execute_query(
                f"""
                UNWIND $rows AS row
                MERGE (n:{label} {{mongo_id: row.mongo_id}})
                SET n = row.props
                """,
                rows=batch,
                database_="neo4j",
            )
        total += len(rows)
        print(f"Neo4j {label:<18} nodos={len(rows)}")
    return total


def cargar_relaciones_neo4j(driver, data):
    relaciones = construir_relaciones(data)
    total = 0
    for (label_a, rel_type, label_b), rows in relaciones.items():
        for batch in por_lotes(rows):
            driver.execute_query(
                f"""
                UNWIND $rows AS row
                MATCH (a:{label_a} {{mongo_id: row.a}})
                MATCH (b:{label_b} {{mongo_id: row.b}})
                MERGE (a)-[:{rel_type}]->(b)
                """,
                rows=batch,
                database_="neo4j",
            )
        total += len(rows)
        print(f"Neo4j {label_a}-{rel_type}->{label_b:<16} relaciones={len(rows)}")
    return total


def construir_relaciones(data):
    rels = {}
    index = indexar_por_tmp_key(data)

    def add(label_a, rel_type, label_b, a_id, b_id):
        if (label_a, rel_type, label_b) not in RELACIONES_NEO_PERMITIDAS:
            raise RuntimeError(f"Relacion Neo4j no permitida: {label_a}-{rel_type}->{label_b}")
        rels.setdefault((label_a, rel_type, label_b), []).append({"a": str(a_id), "b": str(b_id)})

    for doc in data["rallies"]:
        add("Campeonato", "TIENE_RALLY", "Rally", ref(index, doc["__campeonato_key"]), doc["_id"])
        for equipo_key in doc["__equipos_keys"]:
            add("Equipo", "PARTICIPA_EN", "Rally", ref(index, equipo_key), doc["_id"])

    for doc in data["pilotos"]:
        add("Piloto", "PERTENECE_A", "Equipo", doc["_id"], ref(index, doc["__equipo_key"]))
        add("Piloto", "CONDUCE", "Vehiculo", doc["_id"], ref(index, doc["__vehiculo_key"]))

    for idx, doc in enumerate(data["pilotos"]):
        rally = data["rallies"][idx % len(data["rallies"])]
        add("Piloto", "PARTICIPA_EN", "Rally", doc["_id"], rally["_id"])

    for doc in data["copiloto"]:
        add("Copiloto", "PERTENECE_A", "Equipo", doc["_id"], ref(index, doc["__equipo_key"]))
        add("Copiloto", "ASISTE_EN", "Vehiculo", doc["_id"], ref(index, doc["__vehiculo_key"]))

    for idx, doc in enumerate(data["copiloto"]):
        rally = data["rallies"][idx % len(data["rallies"])]
        add("Copiloto", "PARTICIPA_EN", "Rally", doc["_id"], rally["_id"])

    for doc in data["jefe_ingenieria"]:
        add("JefeIngenieria", "DIRIGE", "Equipo", doc["_id"], ref(index, doc["__equipo_key"]))

    for doc in data["vehiculos"]:
        add("Equipo", "USA", "Vehiculo", ref(index, doc["__equipo_key"]), doc["_id"])

    for doc in data["patrocinador"]:
        add("Patrocinador", "PATROCINA", "Equipo", doc["_id"], ref(index, doc["__equipo_key"]))

    for doc in data["resumenes_carrera"]:
        add("ResumenCarrera", "RESUME", "Rally", doc["_id"], ref(index, doc["__rally_key"]))

    return rels


def validar_docs_mongo(data):
    campos_prohibidos = {
        "origen_carga",
        "equipo_id",
        "campeonato_id",
        "piloto_id",
        "copiloto_id",
        "vehiculo_id",
        "rally_id",
        "sponsors",
        "numero_auto",
        "estado",
        "estadisticas",
        "activo",
        "anio_fundacion",
        "anios_experiencia",
        "idiomas",
        "pais_origen",
        "falla_activa",
    }
    for collection, docs in data.items():
        for doc in docs:
            payload = limpiar_doc(doc)
            encontrados = campos_encontrados(payload, campos_prohibidos)
            if encontrados:
                raise RuntimeError(
                    f"Campos no permitidos en MongoDB {collection}/{doc['__tmp_key']}: {sorted(encontrados)}"
                )


def campos_encontrados(value, prohibidos):
    encontrados = set()
    if isinstance(value, dict):
        for key, subvalue in value.items():
            if key in prohibidos:
                encontrados.add(key)
            encontrados.update(campos_encontrados(subvalue, prohibidos))
    elif isinstance(value, list):
        for item in value:
            encontrados.update(campos_encontrados(item, prohibidos))
    return encontrados


def resumen_final(db, driver, data, mongo_summary, neo_nodes, neo_relations):
    print("\nCarga masiva finalizada correctamente.\n")
    print("MongoDB:")
    for collection in MONGO_COLLECTIONS:
        ids = [doc["_id"] for doc in data[collection]]
        count = db[collection].count_documents({"_id": {"$in": ids}})
        inserted = mongo_summary.get(collection, 0)
        print(f"- {collection}: insertados={inserted}, verificados={count}")

    mongo_ids = [str(doc["_id"]) for collection in NEO_LABELS for doc in data[collection]]
    records, _, _ = driver.execute_query(
        """
        MATCH (n)
        WHERE n.mongo_id IN $mongo_ids
        RETURN count(n) AS nodos
        """,
        mongo_ids=mongo_ids,
        database_="neo4j",
    )
    rel_records, _, _ = driver.execute_query(
        """
        MATCH (a)-[r]->(b)
        WHERE a.mongo_id IN $mongo_ids AND b.mongo_id IN $mongo_ids
        RETURN count(r) AS relaciones
        """,
        mongo_ids=mongo_ids,
        database_="neo4j",
    )

    print("\nNeo4j:")
    print(f"- Nodos creados/actualizados: {neo_nodes}")
    print(f"- Relaciones creadas/actualizadas: {neo_relations}")
    print(f"- Nodos verificados: {records[0]['nodos']}")
    print(f"- Relaciones verificadas: {rel_records[0]['relaciones']}")


def ejecutar_carga():
    client = None
    driver = None
    try:
        client = conectar_mongo()
        driver = conectar_neo4j()
        db = client[MONGO_DB]

        data = generar_datos()
        validar_docs_mongo(data)
        limpiar_datos_previos(db, driver)
        mongo_summary = insertar_documentos(db, data)
        guardar_metadata(db, data)

        preparar_neo4j(driver)
        normalizar_nodos_neo4j(driver)
        neo_nodes = cargar_nodos_neo4j(driver, data)
        neo_relations = cargar_relaciones_neo4j(driver, data)
        normalizar_nodos_neo4j(driver)

        resumen_final(db, driver, data, mongo_summary, neo_nodes, neo_relations)
    except Exception as exc:
        print(f"\nERROR durante la carga masiva: {exc}", file=sys.stderr)
        raise
    finally:
        if driver is not None:
            driver.close()
        if client is not None:
            client.close()


if __name__ == "__main__":
    ejecutar_carga()
