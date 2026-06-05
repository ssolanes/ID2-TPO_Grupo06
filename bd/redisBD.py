# bd/redisBD.py
# Definición de estructura Redis y carga de datos iniciales
# No hay DDL formal en Redis, este archivo documenta y crea las keys del proyecto.
#
# Uso directo:  python bd/redisBD.py
# O vía runBD:  python runBD.py --solo redis

import redis
from datetime import datetime

# ─── Conexión ─────────────────────────────────────────────────────────────────

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB   = 0

def get_redis() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )


# ─── Estructura de keys del proyecto ─────────────────────────────────────────
#
#  STRING
#  ──────
#  rally:activo                         → rally_id del rally en curso
#  rally:{rally_id}:estado              → "pendiente" | "en_curso" | "finalizado"
#
#  HASH  (info estática del piloto, replicada desde MongoDB para acceso rápido)
#  ────
#  piloto:{piloto_id}                   → {nombre, equipo, numero, pais}
#
#  SORTED SET  (ranking por tramo — score = tiempo en milisegundos)
#  ──────────
#  timing:{rally_id}:{ss_id}            → ZASET piloto_id → tiempo_ms
#
#  HASH  (tiempos de split dentro de un SS para un piloto)
#  ────
#  splits:{rally_id}:{ss_id}:{piloto_id} → {sp1: tiempo_ms, sp2: tiempo_ms, ...}
#
#  SORTED SET  (clasificación general acumulada del rally)
#  ──────────
#  overall:{rally_id}                   → ZASET piloto_id → tiempo_total_ms
#
#  LIST  (log de eventos en vivo: "piloto llegó a split X")
#  ────
#  eventos:{rally_id}                   → ["{ts}|{piloto_id}|{evento}", ...]
#
#  STRING  (ss actualmente en disputa)
#  ──────
#  ss:activo:{rally_id}                 → ss_id


# ─── Datos de ejemplo ─────────────────────────────────────────────────────────

RALLY_ID = "rally_arg_2026"

PILOTOS = [
    {"id": "wrc_ogier_01",    "nombre": "Sébastien Ogier",  "equipo": "TGR",     "numero": "1",  "pais": "FR"},
    {"id": "wrc_evans_33",    "nombre": "Elfyn Evans",       "equipo": "TGR",     "numero": "33", "pais": "GB"},
    {"id": "wrc_neuville_11", "nombre": "Thierry Neuville",  "equipo": "Hyundai", "numero": "11", "pais": "BE"},
]

# Tiempos en milisegundos por SS y piloto
TIEMPOS_SS = {
    "ss_arg_2026_01": {
        "wrc_ogier_01":    748320,
        "wrc_neuville_11": 749980,
        "wrc_evans_33":    751440,
    },
    "ss_arg_2026_02": {
        "wrc_neuville_11": 901200,
        "wrc_ogier_01":    904800,
        "wrc_evans_33":    909600,
    },
    "ss_arg_2026_03": {
        "wrc_ogier_01":    747100,
        "wrc_neuville_11": 748800,
        "wrc_evans_33":    752900,
    },
}

# Splits (tiempo_ms acumulado al pasar por cada split)
SPLITS = {
    "ss_arg_2026_01": {
        "wrc_ogier_01":    {"sp1": 128400,  "sp2": 405800},
        "wrc_neuville_11": {"sp1": 129100,  "sp2": 407200},
        "wrc_evans_33":    {"sp1": 130500,  "sp2": 410100},
    },
    "ss_arg_2026_02": {
        "wrc_ogier_01":    {"sp1": 178500,  "sp2": 512000},
        "wrc_neuville_11": {"sp1": 177800,  "sp2": 509300},
        "wrc_evans_33":    {"sp1": 181200,  "sp2": 516400},
    },
}

EVENTOS_EJEMPLO = [
    f"{datetime(2026,8,14,9,12,34)}|wrc_ogier_01|Paso por Split 1 · ss_arg_2026_01",
    f"{datetime(2026,8,14,9,12,55)}|wrc_neuville_11|Paso por Split 1 · ss_arg_2026_01",
    f"{datetime(2026,8,14,9,13,5)}|wrc_evans_33|Paso por Split 1 · ss_arg_2026_01",
    f"{datetime(2026,8,14,9,19,22)}|wrc_ogier_01|Llegada · ss_arg_2026_01 · 12:28.320",
    f"{datetime(2026,8,14,9,19,35)}|wrc_neuville_11|Llegada · ss_arg_2026_01 · 12:29.980",
    f"{datetime(2026,8,14,9,19,51)}|wrc_evans_33|Llegada · ss_arg_2026_01 · 12:31.440",
]


# ─── Inicialización ───────────────────────────────────────────────────────────

def init_redis(verbose: bool = True, flush: bool = False):
    r = get_redis()

    if flush:
        r.flushdb()
        if verbose:
            print("  DB flusheada")

    # Rally activo
    r.set("rally:activo", RALLY_ID)
    r.set(f"rally:{RALLY_ID}:estado", "en_curso")
    r.set(f"ss:activo:{RALLY_ID}", "ss_arg_2026_01")

    # Info pilotos (HASH)
    for p in PILOTOS:
        r.hset(f"piloto:{p['id']}", mapping={
            "nombre": p["nombre"],
            "equipo": p["equipo"],
            "numero": p["numero"],
            "pais":   p["pais"],
        })

    # Tiempos por SS (ZASET)
    for ss_id, tiempos in TIEMPOS_SS.items():
        key = f"timing:{RALLY_ID}:{ss_id}"
        r.delete(key)
        r.zadd(key, tiempos)

    # Splits por SS/piloto (HASH)
    for ss_id, pilotos_splits in SPLITS.items():
        for piloto_id, sp in pilotos_splits.items():
            key = f"splits:{RALLY_ID}:{ss_id}:{piloto_id}"
            r.delete(key)
            r.hset(key, mapping={k: str(v) for k, v in sp.items()})

    # Clasificación general acumulada (ZASET — suma de los 3 SS)
    overall_key = f"overall:{RALLY_ID}"
    r.delete(overall_key)
    totales = {}
    for ss_id, tiempos in TIEMPOS_SS.items():
        for piloto_id, t in tiempos.items():
            totales[piloto_id] = totales.get(piloto_id, 0) + t
    r.zadd(overall_key, totales)

    # Log de eventos (LIST)
    eventos_key = f"eventos:{RALLY_ID}"
    r.delete(eventos_key)
    for evento in EVENTOS_EJEMPLO:
        r.rpush(eventos_key, evento)

    if verbose:
        print(f"  rally:activo = {r.get('rally:activo')}")
        for ss_id in TIEMPOS_SS:
            key = f"timing:{RALLY_ID}:{ss_id}"
            print(f"  {key}: {r.zcard(key)} pilotos")
        print(f"  overall:{RALLY_ID}: {r.zcard(overall_key)} pilotos")
        print(f"  eventos:{RALLY_ID}: {r.llen(eventos_key)} eventos")


# ─── Helpers de consulta (reutilizables desde el frontend) ───────────────────

def get_ranking_ss(rally_id: str, ss_id: str) -> list[dict]:
    """Devuelve el ranking de un SS desde Redis."""
    r = get_redis()
    key = f"timing:{rally_id}:{ss_id}"
    items = r.zrange(key, 0, -1, withscores=True)
    resultado = []
    for pos, (piloto_id, tiempo_ms) in enumerate(items, 1):
        info = r.hgetall(f"piloto:{piloto_id}") or {}
        seg = tiempo_ms / 1000
        resultado.append({
            "pos":      pos,
            "piloto_id": piloto_id,
            "nombre":   info.get("nombre", piloto_id),
            "equipo":   info.get("equipo", "—"),
            "numero":   info.get("numero", "—"),
            "tiempo_ms": int(tiempo_ms),
            "tiempo":   f"{int(seg // 60)}:{seg % 60:06.3f}",
        })
    return resultado


def get_clasificacion_general(rally_id: str) -> list[dict]:
    """Clasificación general del rally."""
    r = get_redis()
    key = f"overall:{rally_id}"
    items = r.zrange(key, 0, -1, withscores=True)
    resultado = []
    ref = None
    for pos, (piloto_id, total_ms) in enumerate(items, 1):
        if ref is None:
            ref = total_ms
        info = r.hgetall(f"piloto:{piloto_id}") or {}
        seg = total_ms / 1000
        gap_ms = total_ms - ref
        resultado.append({
            "pos":      pos,
            "piloto_id": piloto_id,
            "nombre":   info.get("nombre", piloto_id),
            "equipo":   info.get("equipo", "—"),
            "tiempo":   f"{int(seg // 60)}:{seg % 60:06.3f}",
            "gap":      "—" if gap_ms == 0 else f"+{gap_ms/1000:.3f}s",
        })
    return resultado


def get_eventos(rally_id: str, ultimos: int = 20) -> list[str]:
    """Últimos N eventos del log."""
    r = get_redis()
    return r.lrange(f"eventos:{rally_id}", -ultimos, -1)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[Redis] Iniciando setup...")
    try:
        init_redis(verbose=True, flush=False)
        print("[Redis] ✓ Listo")
        print("\nEjemplo de consulta:")
        print("  python -c \"from bd.redisBD import get_ranking_ss; "
              "print(get_ranking_ss('rally_arg_2026', 'ss_arg_2026_01'))\"")
    except Exception as e:
        print(f"[Redis] ✗ Error: {e}")
        print("  Verificá que Redis esté corriendo en localhost:6379")