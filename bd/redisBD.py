# Simulador de datos en vivo para Redis.
# En rally no corren todos al mismo tiempo: Redis guarda el auto activo en tramo,
# el ranking acumulado, sesiones activas y el ultimo checkpoint alcanzado.

import redis
import time
import random
import subprocess


REDIS_HOST = "localhost"
REDIS_PORT = 6379
CARRERA = "wrc_2026_finlandia"
PILOTOS = ["p1", "p2", "p3"]
CHECKPOINTS_POR_ETAPA = 8
SEGUNDOS_ENTRE_LARGADAS = 3
TIEMPOS_REFERENCIA = {
    "p1": 1132.450,
    "p2": 1128.920,
    "p3": 1141.300,
}


def piloto_siguiente(indice_actual):
    return PILOTOS[(indice_actual + 1) % len(PILOTOS)]


def conectar_redis():
    subprocess.run(["docker", "start", "redis"], capture_output=True)
    cliente = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    cliente.ping()
    return cliente


def limpiar_estado_vivo(r):
    claves = [
        f"carrera:{CARRERA}:auto:activo",
        f"carrera:{CARRERA}:piloto:activo",
        f"carrera:{CARRERA}:piloto:siguiente",
        f"carrera:{CARRERA}:ranking:vivo",
        f"carrera:{CARRERA}:ranking:referencia",
        f"carrera:{CARRERA}:eventos",
    ]
    claves.extend(f"carrera:{CARRERA}:auto:{piloto}:checkpoint" for piloto in PILOTOS)
    r.delete(*claves)


def sembrar_tiempos_referencia(r):
    r.zadd(f"carrera:{CARRERA}:ranking:referencia", TIEMPOS_REFERENCIA)
    r.zadd(f"carrera:{CARRERA}:ranking:vivo", TIEMPOS_REFERENCIA)


def actualizar_piloto(r, piloto, siguiente, checkpoint, parciales_checkpoint, tiempo_objetivo):
    velocidad = random.randint(90, 185)
    rpm = random.randint(3200, 8700)
    temperatura = round(random.uniform(78, 112), 1)
    latitud = round(61.498 + random.uniform(-0.025, 0.025), 6)
    longitud = round(23.761 + random.uniform(-0.025, 0.025), 6)
    tiempo_total = round(parciales_checkpoint[checkpoint - 1], 3)
    referencia = float(r.zscore(f"carrera:{CARRERA}:ranking:referencia", piloto) or tiempo_objetivo)
    mejora = round(referencia - tiempo_objetivo, 3)

    r.set(f"carrera:{CARRERA}:piloto:activo", piloto)
    r.set(f"carrera:{CARRERA}:piloto:siguiente", siguiente)
    r.hset(f"carrera:{CARRERA}:auto:activo", mapping={
        "piloto": piloto,
        "siguiente_piloto": siguiente,
        "etapa": "SS1",
        "estado_tramo": "en_tramo",
        "velocidad_kmh": velocidad,
        "rpm": rpm,
        "temperatura_motor": temperatura,
        "latitud": latitud,
        "longitud": longitud,
        "ultimo_checkpoint": checkpoint,
        "checkpoints_totales": CHECKPOINTS_POR_ETAPA,
        "tiempo_parcial": tiempo_total,
        "tiempo_proyectado": tiempo_objetivo,
        "referencia_a_superar": referencia,
        "mejora_estimada": mejora,
        "actualizado_en": int(time.time()),
    })
    if checkpoint == CHECKPOINTS_POR_ETAPA:
        r.zadd(f"carrera:{CARRERA}:ranking:vivo", {piloto: tiempo_objetivo})
    r.set(f"carrera:{CARRERA}:auto:{piloto}:checkpoint", checkpoint)
    r.xadd(f"carrera:{CARRERA}:eventos", {
        "piloto": piloto,
        "velocidad_kmh": velocidad,
        "rpm": rpm,
        "temperatura_motor": temperatura,
        "checkpoint": checkpoint,
        "tiempo_total": tiempo_total,
        "tiempo_parcial": tiempo_total,
        "tiempo_proyectado": tiempo_objetivo,
        "referencia_a_superar": referencia,
        "mejora_estimada": mejora,
        "estado_tramo": "en_tramo",
    }, maxlen=1000, approximate=True)


def generar_parciales(tiempo_final):
    pesos = [random.uniform(0.85, 1.15) for _ in range(CHECKPOINTS_POR_ETAPA)]
    total_pesos = sum(pesos)
    parciales = []
    acumulado = 0
    for peso in pesos:
        acumulado += tiempo_final * (peso / total_pesos)
        parciales.append(round(acumulado, 3))
    parciales[-1] = tiempo_final
    return parciales


def main():
    try:
        r = conectar_redis()
    except Exception as e:
        print(f"No se pudo conectar a Redis: {e}")
        return

    limpiar_estado_vivo(r)
    sembrar_tiempos_referencia(r)
    r.sadd(f"carrera:{CARRERA}:usuarios:activos", "admin", "cronometrista", "viewer_01")
    print("Redis en vivo corriendo...")

    indice_piloto = 0
    checkpoint = 1
    tiempos_objetivo = {
        piloto: round(TIEMPOS_REFERENCIA[piloto] - random.uniform(1.5, 18.0), 3)
        for piloto in PILOTOS
    }
    parciales_por_piloto = {
        piloto: generar_parciales(tiempo)
        for piloto, tiempo in tiempos_objetivo.items()
    }

    while True:
        piloto = PILOTOS[indice_piloto]
        siguiente = piloto_siguiente(indice_piloto)
        actualizar_piloto(
            r,
            piloto,
            siguiente,
            checkpoint,
            parciales_por_piloto[piloto],
            tiempos_objetivo[piloto],
        )

        checkpoint += 1
        if checkpoint > CHECKPOINTS_POR_ETAPA:
            r.xadd(f"carrera:{CARRERA}:eventos", {
                "piloto": piloto,
                "checkpoint": CHECKPOINTS_POR_ETAPA,
                "tiempo_total": r.zscore(f"carrera:{CARRERA}:ranking:vivo", piloto) or 0,
                "tiempo_proyectado": tiempos_objetivo[piloto],
                "referencia_a_superar": TIEMPOS_REFERENCIA[piloto],
                "mejora_estimada": round(TIEMPOS_REFERENCIA[piloto] - tiempos_objetivo[piloto], 3),
                "estado_tramo": "finalizado",
            }, maxlen=1000, approximate=True)
            indice_piloto = (indice_piloto + 1) % len(PILOTOS)
            checkpoint = 1
            if indice_piloto == 0:
                tiempos_objetivo = {
                    piloto: round(TIEMPOS_REFERENCIA[piloto] - random.uniform(1.5, 18.0), 3)
                    for piloto in PILOTOS
                }
                parciales_por_piloto = {
                    piloto: generar_parciales(tiempo)
                    for piloto, tiempo in tiempos_objetivo.items()
                }
            time.sleep(SEGUNDOS_ENTRE_LARGADAS)

        time.sleep(1)


if __name__ == "__main__":
    main()
