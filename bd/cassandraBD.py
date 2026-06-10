import os
import subprocess
import time

import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
CASSANDRA_CONTAINER = os.getenv("CASSANDRA_CONTAINER", "cassandra-demo")
CARRERA = "wrc_2026_finlandia"
STREAM_EVENTOS = f"carrera:{CARRERA}:eventos"
KEYSPACE = "world_rally_cup"


def cql_escape(valor):
    return str(valor).replace("'", "''")


def formato_tiempo(segundos):
    total = float(segundos)
    horas = int(total // 3600)
    minutos = int((total % 3600) // 60)
    segundos_restantes = total % 60
    return f"{horas:02d}:{minutos:02d}:{segundos_restantes:06.3f}"


def ejecutar_cql(cql):
    cql = " ".join(line.strip() for line in cql.strip().splitlines() if line.strip())
    comando = ["docker", "exec", CASSANDRA_CONTAINER, "cqlsh", "-e", cql]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip() or resultado.stdout.strip())
    return resultado.stdout


def crear_tablas():
    subprocess.run(["docker", "start", CASSANDRA_CONTAINER], capture_output=True)
    ejecutar_cql(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
    """)
    ejecutar_cql(f"""
        CREATE TABLE IF NOT EXISTS {KEYSPACE}.telemetria_historica (
            carrera text,
            piloto text,
            fecha timestamp,
            velocidad_kmh int,
            rpm int,
            temperatura_motor double,
            checkpoint int,
            PRIMARY KEY ((carrera, piloto), fecha)
        ) WITH CLUSTERING ORDER BY (fecha DESC);
    """)
    ejecutar_cql(f"""
        CREATE TABLE IF NOT EXISTS {KEYSPACE}.tiempos_checkpoint (
            carrera text,
            checkpoint int,
            piloto text,
            fecha timestamp,
            tiempo_total double,
            PRIMARY KEY ((carrera, checkpoint), tiempo_total, piloto)
        );
    """)
    ejecutar_cql(f"""
        CREATE TABLE IF NOT EXISTS {KEYSPACE}.ranking_temporal (
            carrera text,
            fecha timestamp,
            piloto text,
            posicion int,
            tiempo_total double,
            PRIMARY KEY ((carrera), fecha, posicion, piloto)
        ) WITH CLUSTERING ORDER BY (fecha DESC, posicion ASC, piloto ASC);
    """)
    ejecutar_cql(f"""
        CREATE TABLE IF NOT EXISTS {KEYSPACE}.eventos_carrera (
            carrera text,
            fecha timestamp,
            evento_id text,
            piloto text,
            tipo text,
            descripcion text,
            PRIMARY KEY ((carrera), fecha, evento_id)
        ) WITH CLUSTERING ORDER BY (fecha DESC, evento_id ASC);
    """)


def guardar_evento(evento_id, datos):
    piloto = cql_escape(datos.get("piloto", ""))
    checkpoint = int(float(datos.get("checkpoint", 0)))
    tiempo_total = float(datos.get("tiempo_total", 0))
    velocidad = int(float(datos.get("velocidad_kmh", 0)))
    rpm = int(float(datos.get("rpm", 0)))
    temperatura = float(datos.get("temperatura_motor", 0))
    descripcion = cql_escape(
        f"{piloto} paso checkpoint {checkpoint} con {formato_tiempo(tiempo_total)} acumulado"
    )

    ejecutar_cql(f"""
        INSERT INTO {KEYSPACE}.telemetria_historica
        (carrera, piloto, fecha, velocidad_kmh, rpm, temperatura_motor, checkpoint)
        VALUES ('{CARRERA}', '{piloto}', toTimestamp(now()), {velocidad}, {rpm}, {temperatura}, {checkpoint});

        INSERT INTO {KEYSPACE}.tiempos_checkpoint
        (carrera, checkpoint, piloto, fecha, tiempo_total)
        VALUES ('{CARRERA}', {checkpoint}, '{piloto}', toTimestamp(now()), {tiempo_total});

        INSERT INTO {KEYSPACE}.eventos_carrera
        (carrera, fecha, evento_id, piloto, tipo, descripcion)
        VALUES ('{CARRERA}', toTimestamp(now()), '{cql_escape(evento_id)}', '{piloto}', 'telemetria', '{descripcion}');
    """)


def guardar_ranking(r):
    ranking = r.zrange(f"carrera:{CARRERA}:ranking:vivo", 0, -1, withscores=True)
    sentencias = []
    for posicion, (piloto, tiempo_total) in enumerate(ranking, start=1):
        sentencias.append(f"""
            INSERT INTO {KEYSPACE}.ranking_temporal
            (carrera, fecha, piloto, posicion, tiempo_total)
            VALUES ('{CARRERA}', toTimestamp(now()), '{cql_escape(piloto)}', {posicion}, {float(tiempo_total)});
        """)
    if sentencias:
        ejecutar_cql("\n".join(sentencias))


def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    try:
        crear_tablas()
    except Exception as e:
        print(f"No se pudo preparar Cassandra: {e}")
        return

    print("Cassandra historico corriendo...")
    ultimo_id = "0-0"

    while True:
        try:
            mensajes = r.xread({STREAM_EVENTOS: ultimo_id}, block=5000, count=10)
            if not mensajes:
                continue

            for _, eventos in mensajes:
                for evento_id, datos in eventos:
                    guardar_evento(evento_id, datos)
                    ultimo_id = evento_id
            guardar_ranking(r)
        except Exception as e:
            print(f"Error persistiendo en Cassandra: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
