from nicegui import ui
import html
import redis
import subprocess
from frontend_static.shared import GLOBAL_CSS, DARK, RED, BLUE, GREY, CARD, BORDER, GREEN, WHITE, GOLD


REDIS_HOST = "localhost"
REDIS_PORT = 6379
CASSANDRA_CONTAINER = "cassandra-demo"
CARRERA = "wrc_2026_finlandia"
KEYSPACE = "world_rally_cup"
PILOTOS = ["p1", "p2", "p3"]


def redis_cliente():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def ejecutar_cql(cql):
    cql = " ".join(line.strip() for line in cql.strip().splitlines() if line.strip())
    resultado = subprocess.run(
        ["docker", "exec", CASSANDRA_CONTAINER, "cqlsh", "-e", cql],
        capture_output=True,
        text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip() or resultado.stdout.strip())
    return resultado.stdout.strip()


def leer_redis():
    try:
        r = redis_cliente()
        r.ping()
        ranking = r.zrange(f"carrera:{CARRERA}:ranking:vivo", 0, -1, withscores=True)
        referencia = dict(r.zrange(f"carrera:{CARRERA}:ranking:referencia", 0, -1, withscores=True))
        auto_activo = r.hgetall(f"carrera:{CARRERA}:auto:activo")
        usuarios = sorted(r.smembers(f"carrera:{CARRERA}:usuarios:activos"))
        return {
            "ok": True,
            "ranking": ranking,
            "referencia": referencia,
            "auto_activo": auto_activo,
            "usuarios": usuarios,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "ranking": [], "referencia": {}, "auto_activo": {}, "usuarios": []}


def leer_cassandra():
    try:
        ranking = ejecutar_cql(f"""
            SELECT posicion, piloto, tiempo_total
            FROM {KEYSPACE}.ranking_temporal
            WHERE carrera = '{CARRERA}'
            LIMIT 10;
        """)
        eventos = ejecutar_cql(f"""
            SELECT piloto, tipo, descripcion
            FROM {KEYSPACE}.eventos_carrera
            WHERE carrera = '{CARRERA}'
            LIMIT 10;
        """)
        return {
            "ok": True,
            "ranking": parsear_tabla_cql(ranking),
            "eventos": parsear_tabla_cql(eventos),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "ranking": [], "eventos": []}


def parsear_tabla_cql(salida):
    lineas = [linea for linea in salida.splitlines() if "|" in linea]
    if not lineas:
        return []
    encabezados = [columna.strip() for columna in lineas[0].split("|")]
    filas = []
    for linea in lineas[1:]:
        if set(linea.strip()) <= {"-", "+", " "}:
            continue
        valores = [valor.strip() for valor in linea.split("|")]
        if len(valores) == len(encabezados):
            filas.append(dict(zip(encabezados, valores)))
    return filas


def texto_estado(ok, nombre):
    color = GREEN if ok else RED
    estado = "ONLINE" if ok else "SIN CONEXION"
    ui.html(
        f'<div style="font-family:Courier New;color:{color};font-size:0.78rem;'
        f'font-weight:bold;margin-bottom:10px;">{nombre}: {estado}</div>'
    )


def fila_dato(label, valor, color=WHITE):
    with ui.row().classes("w-full justify-between").style("gap:10px; flex-wrap:nowrap;"):
        ui.label(label).style(f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.78rem;")
        ui.label(str(valor)).style(
            f"font-family:'Courier New',monospace; color:{color}; font-size:0.78rem; "
            f"font-weight:bold; text-align:right; overflow-wrap:anywhere;"
        )


def bloque_pre(texto):
    texto = html.escape(texto or "")
    ui.html(
        f'<pre style="font-family:Courier New;color:{WHITE};font-size:0.72rem;'
        f'white-space:pre-wrap;overflow:auto;max-height:180px;width:100%;'
        f'box-sizing:border-box;margin:6px 0 0 0;">{texto}</pre>'
    )


def formato_tiempo(segundos):
    try:
        total = float(segundos)
    except (TypeError, ValueError):
        return "-"
    horas = int(total // 3600)
    minutos = int((total % 3600) // 60)
    segundos_restantes = total % 60
    return f"{horas:02d}:{minutos:02d}:{segundos_restantes:06.3f}"


def formato_diferencia(segundos):
    try:
        total = float(segundos)
    except (TypeError, ValueError):
        return "-"
    signo = "+" if total >= 0 else "-"
    return f"{signo}{formato_tiempo(abs(total))}"


@ui.page("/")
def index():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK}; margin:0; padding:24px; box-sizing:border-box;")

    redis_box = None
    autos_box = None
    cassandra_box = None

    with ui.row().style("width:100%; gap:16px; margin-top:20px; min-height:380px; flex-wrap:wrap; align-items:stretch;"):
        with ui.card().style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
            f"flex:2; min-width:320px; padding:20px; box-shadow:none; overflow:hidden;"
        ):
            ui.label("World Rally Cup · Vivo").style(
                f"font-family:'Courier New',monospace; color:{WHITE}; font-size:1rem; font-weight:bold;"
            )
            ui.label("Panel operativo para tramo activo, tiempos acumulados e historico.").style(
                f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.8rem;"
            )

        with ui.card().style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
            f"flex:1; min-width:280px; padding:20px; box-shadow:none; overflow:hidden;"
        ):
            ui.label("Redis · Ranking en vivo").style(
                f"font-family:'Courier New',monospace; color:{WHITE}; font-size:0.9rem; font-weight:bold;"
            )
            redis_box = ui.column().classes("w-full").style("overflow:hidden;")

        with ui.card().style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
            f"flex:1; min-width:280px; padding:20px; box-shadow:none; overflow:hidden;"
        ):
            ui.label("Redis · Auto en tramo").style(
                f"font-family:'Courier New',monospace; color:{WHITE}; font-size:0.9rem; font-weight:bold;"
            )
            autos_box = ui.column().classes("w-full").style("overflow:hidden;")

    with ui.card().style(
        f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
        f"width:100%; min-height:200px; margin-top:16px; padding:20px; box-shadow:none; overflow:hidden;"
    ):
        ui.label("Cassandra · Historico").style(
            f"font-family:'Courier New',monospace; color:{WHITE}; font-size:0.9rem; font-weight:bold;"
        )
        cassandra_box = ui.column().classes("w-full").style("overflow:hidden;")

    def actualizar():
        datos_redis = leer_redis()
        redis_box.clear()
        autos_box.clear()

        with redis_box:
            texto_estado(datos_redis["ok"], "Redis")
            if not datos_redis["ok"]:
                ui.label(datos_redis["error"]).style(f"font-family:'Courier New',monospace; color:{RED}; font-size:0.72rem;")
            for posicion, (piloto, tiempo) in enumerate(datos_redis["ranking"], start=1):
                ref = datos_redis["referencia"].get(piloto)
                delta = f" ({formato_diferencia(tiempo - ref)})" if ref is not None else ""
                color = GREEN if ref is not None and tiempo < ref else GOLD if posicion == 1 else WHITE
                fila_dato(f"{posicion}. {piloto}", f"{formato_tiempo(tiempo)}{delta}", color)
            fila_dato("Usuarios activos", len(datos_redis["usuarios"]), GREEN)

        with autos_box:
            texto_estado(datos_redis["ok"], "Redis")
            auto = datos_redis["auto_activo"]
            if auto:
                fila_dato("Piloto", auto.get("piloto", "-"), GOLD)
                fila_dato("Siguiente", auto.get("siguiente_piloto", "-"), WHITE)
                fila_dato("Etapa", auto.get("etapa", "-"), BLUE)
                fila_dato("Estado", auto.get("estado_tramo", "-"), GREEN)
                fila_dato("Velocidad", f'{auto.get("velocidad_kmh", "-")} km/h')
                fila_dato("RPM", auto.get("rpm", "-"))
                fila_dato("Temperatura", f'{auto.get("temperatura_motor", "-")} C')
                fila_dato("GPS", f'{auto.get("latitud", "-")}, {auto.get("longitud", "-")}')
                fila_dato("Parcial", formato_tiempo(auto.get("tiempo_parcial")), WHITE)
                fila_dato("Referencia", formato_tiempo(auto.get("referencia_a_superar")), GOLD)
                fila_dato("Proyectado", formato_tiempo(auto.get("tiempo_proyectado")), WHITE)
                fila_dato("Mejora estimada", formato_diferencia(-float(auto.get("mejora_estimada", 0))), GREEN)
                fila_dato(
                    "Checkpoint",
                    f'{auto.get("ultimo_checkpoint", "-")}/{auto.get("checkpoints_totales", "-")}',
                    GREEN,
                )
            else:
                ui.label("Sin auto activo en tramo. Ejecuta redisBD.py para generar datos.").style(
                    f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.78rem;"
                )

        datos_cassandra = leer_cassandra()
        cassandra_box.clear()
        with cassandra_box:
            texto_estado(datos_cassandra["ok"], "Cassandra")
            if not datos_cassandra["ok"]:
                ui.label(datos_cassandra["error"]).style(f"font-family:'Courier New',monospace; color:{RED}; font-size:0.72rem;")
                return

            with ui.row().classes("w-full gap-4").style("align-items:flex-start;"):
                with ui.column().style("flex:1; min-width:300px;"):
                    ui.label("Ranking temporal guardado").style(
                        f"font-family:'Courier New',monospace; color:{BLUE}; font-size:0.8rem; font-weight:bold;"
                    )
                    for fila in datos_cassandra["ranking"][:5]:
                        fila_dato(
                            f'{fila.get("posicion", "-")}. {fila.get("piloto", "-")}',
                            formato_tiempo(fila.get("tiempo_total")),
                        )

                with ui.column().style("flex:1; min-width:300px;"):
                    ui.label("Eventos de carrera").style(
                        f"font-family:'Courier New',monospace; color:{BLUE}; font-size:0.8rem; font-weight:bold;"
                    )
                    for evento in datos_cassandra["eventos"][:5]:
                        fila_dato(evento.get("piloto", "-"), evento.get("descripcion", "-"))

    actualizar()
    ui.timer(2.0, actualizar)


ui.run(
    host="0.0.0.0",
    port=8082,
    title="WRC Realtime · Redis + Cassandra",
    reload=False,
    show=False,
)