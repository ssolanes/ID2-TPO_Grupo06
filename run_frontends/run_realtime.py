from nicegui import ui
import asyncio
import html
import os
import redis
import subprocess
from frontend_static.shared import GLOBAL_CSS, DARK, RED, BLUE, GREY, CARD, BORDER, GREEN, WHITE, GOLD


REDIS_HOST = "localhost"
REDIS_PORT = 6379
CASSANDRA_CONTAINER = os.getenv("CASSANDRA_CONTAINER", "cassandra")
CARRERA = "wrc_2026_finlandia"
KEYSPACE = "world_rally_cup"
PILOTOS = ["p1","p2","p3"]
CHECKPOINTS_POR_ETAPA = 8
TELEMETRIA_POR_PILOTO = 2


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


def es_telemetria_valida(fila):
    try:
        return (
            int(float(fila.get("velocidad_kmh", 0))) > 0
            and int(float(fila.get("rpm", 0))) > 0
            and float(fila.get("temperatura_motor", 0)) > 0
        )
    except (TypeError, ValueError):
        return False


def leer_cassandra():
    try:
        checkpoints_cql = ", ".join(str(numero) for numero in range(1, CHECKPOINTS_POR_ETAPA + 1))

        telemetria_filas = []
        for piloto in PILOTOS:
            telemetria = ejecutar_cql(f"""
                SELECT piloto, fecha, velocidad_kmh, rpm, temperatura_motor, checkpoint
                FROM {KEYSPACE}.telemetria_historica
                WHERE carrera = '{CARRERA}' AND piloto = '{piloto}'
                LIMIT {TELEMETRIA_POR_PILOTO};
            """)
            telemetria_filas.extend(
                fila for fila in parsear_tabla_cql(telemetria) if es_telemetria_valida(fila)
            )

        tiempos = ejecutar_cql(f"""
            SELECT checkpoint, piloto, tiempo_total
            FROM {KEYSPACE}.tiempos_checkpoint
            WHERE carrera = '{CARRERA}' AND checkpoint IN ({checkpoints_cql})
            LIMIT 12;
        """)
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
            "telemetria": telemetria_filas,
            "tiempos": parsear_tabla_cql(tiempos),
            "ranking": parsear_tabla_cql(ranking),
            "eventos": parsear_tabla_cql(eventos),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "telemetria": [], "tiempos": [], "ranking": [], "eventos": []}


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


def mini_panel(titulo, subtitulo=None):
    panel = ui.column().classes("w-full").style(
        f"background:#1C1C24; border:1px solid {BORDER}; border-radius:8px; "
        f"padding:14px; gap:8px; min-height:168px; overflow:hidden;"
    )
    with panel:
        ui.label(titulo).style(
            f"font-family:'Courier New',monospace; color:{BLUE}; "
            f"font-size:0.78rem; font-weight:bold; text-transform:uppercase;"
        )
        if subtitulo:
            ui.label(subtitulo).style(
                f"font-family:'Courier New',monospace; color:{GREY}; "
                f"font-size:0.68rem; margin-top:-4px;"
            )
    return panel


def fila_tabla(columnas):
    with ui.row().classes("w-full items-center").style(
        f"gap:10px; flex-wrap:nowrap; border-top:1px solid {BORDER}; padding-top:7px;"
    ):
        for texto, color, flex in columnas:
            ui.label(str(texto)).style(
                f"font-family:'Courier New',monospace; color:{color}; font-size:0.72rem; "
                f"font-weight:bold; flex:{flex}; overflow:hidden; text-overflow:ellipsis; "
                f"white-space:nowrap;"
            )


def texto_vacio(mensaje):
    ui.label(mensaje).style(
        f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.72rem; "
        f"padding-top:8px;"
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

    # Custom Header with back button
    with ui.row().classes("w-full items-center justify-between").style("margin-bottom: 20px;"):
        ui.html(
            f'<div style="font-family:Courier New; font-size:1.8rem; font-weight:bold; color:{RED};">'
            f'WRC REALTIME · <span style="font-size:0.9rem; color:{GREY};">Telemetría y Datos en Vivo</span>'
            f'</div>'
        )
        ui.link("← Volver", "http://localhost:8080").style(
            f"color:{GREY}; font-family:Courier New; font-weight:bold; border:1px solid {BORDER}; border-radius:6px; padding:6px 16px; text-decoration:none;"
        )

    redis_box = None
    autos_box = None
    cassandra_box = None
    live_overlay_box = None

    with ui.row().style("width:100%; gap:16px; margin-top:20px; min-height:380px; flex-wrap:wrap; align-items:stretch;"):
        with ui.card().style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
            f"flex:2; min-width:320px; padding:20px; box-shadow:none; overflow:hidden;"
        ):
            ui.label("World Rally Cup · Vivo").style(
                f"font-family:'Courier New',monospace; color:{WHITE}; font-size:1rem; font-weight:bold;"
            )
            ui.label("").style(
                f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.8rem;"
            )
            
            ui.image("https://media.tenor.com/iIV83CYgYWgAAAAM/cat-drive-car-cat-monkey-drift.gif").style(
                "width: 100%; max-height: 280px; border-radius: 8px; margin-top: 10px; object-fit: cover;"
            )
            
            live_overlay_box = ui.column().classes("w-full items-center").style("margin-top: 15px; gap: 12px;")
            
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
            f"flex:1; min-width:280px; padding:20px; box-shadow:none; overflow:hidden;"
        ):
            ui.label("Redis · Ranking en vivo").style(
                f"font-family:'Courier New',monospace; color:{WHITE}; font-size:0.9rem; font-weight:bold;"
            )
            redis_box = ui.column().classes("w-full").style("overflow:hidden;")


    with ui.card().style(
        f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
        f"width:100%; min-height:200px; margin-top:16px; padding:20px; box-shadow:none; overflow:hidden;"
    ):
        ui.label("Cassandra · Historico").style(
            f"font-family:'Courier New',monospace; color:{WHITE}; font-size:0.9rem; font-weight:bold;"
        )
        cassandra_box = ui.column().classes("w-full").style("overflow:hidden;")

    async def actualizar_redis():
        datos_redis = await asyncio.to_thread(leer_redis)
        redis_box.clear()
        autos_box.clear()
        live_overlay_box.clear()

        auto = datos_redis["auto_activo"]

        with live_overlay_box:
            if auto:
                piloto_act = auto.get("piloto", "-")
                vel_act = f'{auto.get("velocidad_kmh", "-")} km/h'
                check_act = f'{auto.get("ultimo_checkpoint", "-")}/{auto.get("checkpoints_totales", "-")}'
            else:
                piloto_act, vel_act, check_act = "-", "- km/h", "-/-"

            ui.label(f"Piloto actual: {piloto_act}").style(
                f"font-family:'Courier New',monospace; color:{WHITE}; font-size:1.1rem; font-weight:bold; text-align:center;"
            )
            
            with ui.row().classes("w-full justify-around items-center").style("margin-top: 5px;"):
                with ui.column().classes("items-center"):
                    ui.label("Velocidad").style(f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.9rem;")
                    ui.label(vel_act).style(f"font-family:'Courier New',monospace; color:{WHITE}; font-size:2.4rem; font-weight:bold;")
                
                with ui.column().classes("items-center"):
                    ui.label("Checkpoint").style(f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.9rem;")
                    ui.label(check_act).style(f"font-family:'Courier New',monospace; color:{GREEN}; font-size:2.4rem; font-weight:bold;")

        with redis_box:
            texto_estado(datos_redis["ok"], "Redis")
            if not datos_redis["ok"]:
                ui.label(datos_redis["error"]).style(f"font-family:'Courier New',monospace; color:{RED}; font-size:0.72rem;")
            for posicion, (piloto, tiempo) in enumerate(datos_redis["ranking"], start=1):
                ref = datos_redis["referencia"].get(piloto)
                delta = f" ({formato_diferencia(tiempo - ref)})" if ref is not None else ""
                color = GREEN if ref is not None and tiempo < ref else GOLD if posicion == 1 else WHITE
                fila_dato(f"{posicion}. {piloto}", f"{formato_tiempo(tiempo)}{delta}", color)
            #fila_dato("Usuarios activos", len(datos_redis["usuarios"]), GREEN)

        with autos_box:
            texto_estado(datos_redis["ok"], "Redis")
            if auto:
                fila_dato("Piloto", auto.get("piloto", "-"), GOLD)
                fila_dato("Siguiente", auto.get("siguiente_piloto", "-"), WHITE)
                fila_dato("Etapa", auto.get("etapa", "-"), BLUE)
                estado_original = auto.get("estado_tramo", "-")
                estado_mostrar = "En tramo" if estado_original == "en_tramo" else "Detenido"
                fila_dato("Estado", estado_mostrar, GREEN)
                #fila_dato("Velocidad", f'{auto.get("velocidad_kmh", "-")} km/h')
                fila_dato("RPM", auto.get("rpm", "-"))
                fila_dato("Temperatura", f'{auto.get("temperatura_motor", "-")} C')
                fila_dato("GPS", f'{auto.get("latitud", "-")}, {auto.get("longitud", "-")}')
                fila_dato("Parcial", formato_tiempo(auto.get("tiempo_parcial")), WHITE)
                fila_dato("Referencia", formato_tiempo(auto.get("referencia_a_superar")), GOLD)
                fila_dato("Proyectado", formato_tiempo(auto.get("tiempo_proyectado")), WHITE)
                fila_dato("Mejora estimada", formato_diferencia(-float(auto.get("mejora_estimada", 0))), GREEN)
                # fila_dato(
                #     "Checkpoint",
                #     f'{auto.get("ultimo_checkpoint", "-")}/{auto.get("checkpoints_totales", "-")}',
                #     GREEN,
                # )
            else:
                ui.label("Sin auto activo en tramo. Ejecuta redisBD.py para generar datos.").style(
                    f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.78rem;"
                )

    async def actualizar_cassandra():
        datos_cassandra = await asyncio.to_thread(leer_cassandra)
        cassandra_box.clear()
        with cassandra_box:
            texto_estado(datos_cassandra["ok"], "Cassandra")
            if not datos_cassandra["ok"]:
                ui.label(datos_cassandra["error"]).style(f"font-family:'Courier New',monospace; color:{RED}; font-size:0.72rem;")
                return

            with ui.grid(columns=2).classes("w-full").style(
                "gap:14px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));"
            ):
                with mini_panel("Telemetria historica", "tabla: telemetria_historica"):
                    if not datos_cassandra["telemetria"]:
                        texto_vacio("Sin telemetria historica guardada.")
                    for fila in datos_cassandra["telemetria"][:6]:
                        fila_tabla([
                            (fila.get("piloto", "-"), GOLD, "0 0 46px"),
                            (f'{fila.get("velocidad_kmh", "-")} km/h', WHITE, "1"),
                            (f'{fila.get("rpm", "-")} rpm', WHITE, "1"),
                            (f'{fila.get("temperatura_motor", "-")} C', GREEN, "1"),
                            (f'CP {fila.get("checkpoint", "-")}', BLUE, "0 0 52px"),
                        ])

                with mini_panel("Tiempos por checkpoint", "tabla: tiempos_checkpoint"):
                    if not datos_cassandra["tiempos"]:
                        texto_vacio("Sin tiempos por checkpoint guardados.")
                    for fila in datos_cassandra["tiempos"][:6]:
                        fila_tabla([
                            (f'CP {fila.get("checkpoint", "-")}', BLUE, "0 0 58px"),
                            (fila.get("piloto", "-"), GOLD, "0 0 54px"),
                            (formato_tiempo(fila.get("tiempo_total")), WHITE, "1"),
                        ])

                with mini_panel("Ranking temporal guardado", "tabla: ranking_temporal"):
                    if not datos_cassandra["ranking"]:
                        texto_vacio("Sin ranking temporal guardado.")
                    for fila in datos_cassandra["ranking"][:6]:
                        fila_tabla([
                            (f'{fila.get("posicion", "-")}.', BLUE, "0 0 36px"),
                            (fila.get("piloto", "-"), GOLD, "0 0 54px"),
                            (formato_tiempo(fila.get("tiempo_total")), WHITE, "1"),
                        ])

                with mini_panel("Eventos de carrera", "tabla: eventos_carrera"):
                    if not datos_cassandra["eventos"]:
                        texto_vacio("Sin eventos de carrera guardados.")
                    for evento in datos_cassandra["eventos"][:5]:
                        descripcion = evento.get("descripcion", "-")
                        ui.label(descripcion).style(
                            f"font-family:'Courier New',monospace; color:{WHITE}; "
                            f"font-size:0.72rem; font-weight:bold; border-top:1px solid {BORDER}; "
                            f"padding-top:7px; overflow-wrap:anywhere;"
                        )


    ui.timer(0.1, actualizar_redis, once=True)
    ui.timer(0.2, actualizar_cassandra, once=True)
    ui.timer(1.0, actualizar_redis)
    ui.timer(4.0, actualizar_cassandra)


ui.run(
    host="0.0.0.0",
    port=8082,
    title="WRC Realtime · Redis + Cassandra",
    reload=False,
    show=False,
)
