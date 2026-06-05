# bd/cassandraBD.py
# Definición del schema Cassandra y carga de datos iniciales
# Keyspace: wrc_telemetria
#
# Uso directo:  python bd/cassandraBD.py
# O vía runBD:  python runBD.py --solo cassandra

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime, timedelta
import random

# ─── Conexión ─────────────────────────────────────────────────────────────────

CASSANDRA_HOST    = "127.0.0.1"
CASSANDRA_PORT    = 9042
KEYSPACE          = "wrc_telemetria"

# Descomentá si tu instancia requiere autenticación:
# AUTH = PlainTextAuthProvider("cassandra", "cassandra")

def get_session():
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    # cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, auth_provider=AUTH)
    return cluster, cluster.connect()


# ─── DDL ──────────────────────────────────────────────────────────────────────

DDL_KEYSPACE = f"""
CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
AND durable_writes = true;
"""

# Tabla principal: telemetría por (rally, ss, piloto) ordenada por timestamp DESC
# Partition key compuesta → permite consultas eficientes por rally+ss+piloto
# Clustering key timestamp DESC → el dato más reciente primero (útil para live)
DDL_TELEMETRIA_AUTO = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE}.telemetria_auto (
    rally_id        TEXT,
    ss_id           TEXT,
    piloto_id       TEXT,
    timestamp       TIMESTAMP,
    velocidad       FLOAT,
    rpm             INT,
    marcha          INT,
    aceleracion     FLOAT,
    frenada         FLOAT,
    direccion       FLOAT,
    lat             DOUBLE,
    lon             DOUBLE,
    PRIMARY KEY ((rally_id, ss_id, piloto_id), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
  AND comment = 'Telemetría en tiempo real por rally/ss/piloto';
"""

# Tabla secundaria: tiempos de split por piloto en cada SS
# Permite reconstruir el timeline de parciales
DDL_TIEMPOS_SPLIT = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE}.tiempos_split (
    rally_id        TEXT,
    ss_id           TEXT,
    piloto_id       TEXT,
    split_id        TEXT,
    timestamp       TIMESTAMP,
    tiempo_ms       BIGINT,
    velocidad_paso  FLOAT,
    PRIMARY KEY ((rally_id, ss_id, piloto_id), split_id)
) WITH comment = 'Tiempo de paso por cada split dentro de un SS';
"""

# Tabla de resumen por SS: tiempo final de cada piloto
DDL_RESULTADO_SS = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE}.resultado_ss (
    rally_id        TEXT,
    ss_id           TEXT,
    piloto_id       TEXT,
    tiempo_total_ms BIGINT,
    penalizacion_ms BIGINT,
    tiempo_neto_ms  BIGINT,
    posicion        INT,
    timestamp_fin   TIMESTAMP,
    PRIMARY KEY ((rally_id, ss_id), tiempo_neto_ms, piloto_id)
) WITH CLUSTERING ORDER BY (tiempo_neto_ms ASC, piloto_id ASC)
  AND comment = 'Resultado final de cada piloto en un SS (ordenado por tiempo)';
"""


# ─── Datos de ejemplo ─────────────────────────────────────────────────────────

PILOTOS = [
    {"id": "wrc_ogier_01",    "nombre": "Sébastien Ogier"},
    {"id": "wrc_evans_33",    "nombre": "Elfyn Evans"},
    {"id": "wrc_neuville_11", "nombre": "Thierry Neuville"},
]

SS_IDS = [
    "ss_arg_2026_01",  # Ascochinga 1
    "ss_arg_2026_02",  # El Cóndor 1
    "ss_arg_2026_03",  # Ascochinga 2
]

RALLY_ID = "rally_arg_2026"

# Coordenadas base aproximadas (Villa Carlos Paz, Córdoba)
BASE_LAT = -31.4201
BASE_LON = -64.1888


def _generar_telemetria(session, rally_id: str, ss_id: str, piloto_id: str,
                        base_ts: datetime, n_puntos: int = 30):
    """Genera n_puntos de telemetría simulada para un piloto en un SS."""
    stmt = session.prepare(f"""
        INSERT INTO {KEYSPACE}.telemetria_auto
        (rally_id, ss_id, piloto_id, timestamp,
         velocidad, rpm, marcha, aceleracion, frenada, direccion, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    # Simulación simplificada: aceleración → velocidad máxima → frenada
    fase = "aceleracion"
    vel = 60.0

    for i in range(n_puntos):
        ts = base_ts + timedelta(seconds=i * 2)

        if i < n_puntos * 0.4:
            fase = "aceleracion"
        elif i < n_puntos * 0.7:
            fase = "crucero"
        else:
            fase = "frenada"

        if fase == "aceleracion":
            vel = min(vel + random.uniform(8, 18), 185.0)
            acel = round(random.uniform(65, 100), 1)
            freno = 0.0
            marcha = min(int(vel / 30) + 1, 6)
        elif fase == "crucero":
            vel += random.uniform(-5, 5)
            vel = max(120.0, min(vel, 185.0))
            acel = round(random.uniform(40, 75), 1)
            freno = 0.0
            marcha = 5 if vel > 140 else 4
        else:
            vel = max(vel - random.uniform(10, 25), 40.0)
            acel = 0.0
            freno = round(random.uniform(50, 100), 1)
            marcha = max(int(vel / 35), 1)

        rpm = int(vel * 40 + random.randint(-300, 300))
        rpm = max(1200, min(rpm, 7800))
        direccion = round(random.uniform(-15, 15), 1)
        lat = round(BASE_LAT + i * 0.0004 + random.uniform(-0.00005, 0.00005), 6)
        lon = round(BASE_LON + i * 0.0003 + random.uniform(-0.00005, 0.00005), 6)

        session.execute(stmt, (
            rally_id, ss_id, piloto_id, ts,
            round(vel, 1), rpm, marcha,
            acel, freno, direccion, lat, lon
        ))


def _generar_splits(session, rally_id: str, ss_id: str, piloto_id: str,
                    tiempo_base_ms: int):
    """Genera tiempos de split para 2 splits por SS."""
    stmt = session.prepare(f"""
        INSERT INTO {KEYSPACE}.tiempos_split
        (rally_id, ss_id, piloto_id, split_id, timestamp, tiempo_ms, velocidad_paso)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    sp1_ms = int(tiempo_base_ms * 0.35 + random.randint(-800, 800))
    sp2_ms = int(tiempo_base_ms * 0.70 + random.randint(-600, 600))
    ts = datetime.utcnow()

    session.execute(stmt, (rally_id, ss_id, piloto_id, f"{ss_id}_sp1",
                           ts, sp1_ms, round(random.uniform(130, 165), 1)))
    session.execute(stmt, (rally_id, ss_id, piloto_id, f"{ss_id}_sp2",
                           ts + timedelta(seconds=1), sp2_ms,
                           round(random.uniform(120, 155), 1)))


def _generar_resultados(session, rally_id: str, ss_id: str):
    """Genera resultados finales por SS con tiempos realistas."""
    stmt = session.prepare(f"""
        INSERT INTO {KEYSPACE}.resultado_ss
        (rally_id, ss_id, piloto_id, tiempo_total_ms, penalizacion_ms,
         tiempo_neto_ms, posicion, timestamp_fin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)

    # Tiempos base en ms (entre 11 y 14 minutos para un SS de ~18 km)
    tiempos = {
        "wrc_ogier_01":    748320,
        "wrc_neuville_11": 749980,
        "wrc_evans_33":    751440,
    }
    # Pequeña variación por SS
    variacion = {"ss_arg_2026_01": 0, "ss_arg_2026_02": 5000, "ss_arg_2026_03": -1200}
    delta = variacion.get(ss_id, 0)

    ordenados = sorted(tiempos.items(), key=lambda x: x[1] + delta)
    ts = datetime.utcnow()

    for pos, (piloto_id, t_ms) in enumerate(ordenados, 1):
        t_total = t_ms + delta + random.randint(-200, 200)
        penalizacion = 0
        session.execute(stmt, (
            rally_id, ss_id, piloto_id,
            t_total, penalizacion, t_total + penalizacion,
            pos, ts
        ))


# ─── Inicialización principal ─────────────────────────────────────────────────

def init_cassandra(verbose: bool = True):
    cluster, session = get_session()

    try:
        if verbose:
            print("  Creando keyspace...")
        session.execute(DDL_KEYSPACE)
        session.set_keyspace(KEYSPACE)

        if verbose:
            print("  Creando tablas...")
        session.execute(DDL_TELEMETRIA_AUTO)
        session.execute(DDL_TIEMPOS_SPLIT)
        session.execute(DDL_RESULTADO_SS)

        if verbose:
            print("  Insertando datos de ejemplo...")

        base_ts = datetime(2026, 8, 14, 9, 0, 0)

        for ss_idx, ss_id in enumerate(SS_IDS):
            ss_ts = base_ts + timedelta(hours=ss_idx * 2)
            for piloto in PILOTOS:
                _generar_telemetria(
                    session, RALLY_ID, ss_id, piloto["id"],
                    base_ts=ss_ts + timedelta(minutes=PILOTOS.index(piloto) * 3),
                    n_puntos=30
                )
                _generar_splits(session, RALLY_ID, ss_id, piloto["id"],
                                tiempo_base_ms=748000 + ss_idx * 5000)
            _generar_resultados(session, RALLY_ID, ss_id)

        # Verificar
        if verbose:
            n_telem = session.execute(
                "SELECT COUNT(*) FROM telemetria_auto"
            ).one()[0]
            n_splits = session.execute(
                "SELECT COUNT(*) FROM tiempos_split"
            ).one()[0]
            n_res = session.execute(
                "SELECT COUNT(*) FROM resultado_ss"
            ).one()[0]
            print(f"  telemetria_auto : {n_telem} filas")
            print(f"  tiempos_split   : {n_splits} filas")
            print(f"  resultado_ss    : {n_res} filas")

    finally:
        cluster.shutdown()


# ─── Helpers de consulta (reutilizables desde el frontend) ───────────────────

def consultar_telemetria(rally_id: str, ss_id: str, piloto_id: str,
                         limite: int = 50) -> list[dict]:
    cluster, session = get_session()
    session.set_keyspace(KEYSPACE)
    try:
        rows = session.execute(
            "SELECT * FROM telemetria_auto "
            "WHERE rally_id=%s AND ss_id=%s AND piloto_id=%s LIMIT %s",
            (rally_id, ss_id, piloto_id, limite)
        )
        return [dict(r._asdict()) for r in rows]
    finally:
        cluster.shutdown()


def consultar_splits(rally_id: str, ss_id: str, piloto_id: str) -> list[dict]:
    cluster, session = get_session()
    session.set_keyspace(KEYSPACE)
    try:
        rows = session.execute(
            "SELECT * FROM tiempos_split "
            "WHERE rally_id=%s AND ss_id=%s AND piloto_id=%s",
            (rally_id, ss_id, piloto_id)
        )
        return [dict(r._asdict()) for r in rows]
    finally:
        cluster.shutdown()


def consultar_resultado_ss(rally_id: str, ss_id: str) -> list[dict]:
    """Devuelve el podio de un SS ordenado por tiempo_neto_ms ASC."""
    cluster, session = get_session()
    session.set_keyspace(KEYSPACE)
    try:
        rows = session.execute(
            "SELECT * FROM resultado_ss WHERE rally_id=%s AND ss_id=%s",
            (rally_id, ss_id)
        )
        return [dict(r._asdict()) for r in rows]
    finally:
        cluster.shutdown()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[Cassandra] Iniciando setup...")
    try:
        init_cassandra(verbose=True)
        print("[Cassandra] ✓ Listo")
        print(f"\nEjemplo de consulta:")
        print(f"  python -c \"from bd.cassandraBD import consultar_resultado_ss; "
              f"print(consultar_resultado_ss('rally_arg_2026', 'ss_arg_2026_01'))\"")
    except Exception as e:
        print(f"[Cassandra] ✗ Error: {e}")
        print("  Verificá que Cassandra esté corriendo en 127.0.0.1:9042")
