# frontend_realtime/pages/telemetria.py
# Telemetría de vehículos · Cassandra
# Tabla Cassandra (keyspace: wrc_telemetria):
#
#   CREATE TABLE telemetria_auto (
#     rally_id     TEXT,
#     ss_id        TEXT,
#     piloto_id    TEXT,
#     timestamp    TIMESTAMP,
#     velocidad    FLOAT,
#     rpm          INT,
#     marcha       INT,
#     aceleracion  FLOAT,
#     frenada      FLOAT,
#     lat          DOUBLE,
#     lon          DOUBLE,
#     PRIMARY KEY ((rally_id, ss_id, piloto_id), timestamp)
#   ) WITH CLUSTERING ORDER BY (timestamp DESC);

from nicegui import ui
from frontend_realtime.shared import (
    get_cassandra, cassandra_query, sidebar, GLOBAL_CSS,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK
)


# ─── helpers Cassandra ────────────────────────────────────────────────────────

def _cargar_telemetria(rally_id: str, ss_id: str, piloto_id: str, limite: int = 50) -> list[dict]:
    try:
        rows = cassandra_query(
            "SELECT timestamp, velocidad, rpm, marcha, aceleracion, frenada, lat, lon "
            "FROM telemetria_auto "
            "WHERE rally_id=%s AND ss_id=%s AND piloto_id=%s "
            "LIMIT %s",
            (rally_id, ss_id, piloto_id, limite)
        )
        return [
            {
                "timestamp":   str(r.timestamp)[:19] if r.timestamp else "—",
                "velocidad":   f"{r.velocidad:.1f}" if r.velocidad is not None else "—",
                "rpm":         r.rpm or "—",
                "marcha":      r.marcha or "—",
                "aceleracion": f"{r.aceleracion:.2f}" if r.aceleracion is not None else "—",
                "frenada":     f"{r.frenada:.2f}" if r.frenada is not None else "—",
                "lat":         f"{r.lat:.6f}" if r.lat is not None else "—",
                "lon":         f"{r.lon:.6f}" if r.lon is not None else "—",
            }
            for r in rows
        ]
    except Exception as e:
        return [{"error": str(e)}]


def _insertar_muestra(rally_id, ss_id, piloto_id, velocidad, rpm, marcha, aceleracion, frenada, lat, lon):
    """Inserta un registro de telemetría de prueba."""
    from datetime import datetime
    cassandra_query(
        "INSERT INTO telemetria_auto "
        "(rally_id, ss_id, piloto_id, timestamp, velocidad, rpm, marcha, aceleracion, frenada, lat, lon) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (rally_id, ss_id, piloto_id, datetime.utcnow(),
         float(velocidad), int(rpm), int(marcha),
         float(aceleracion), float(frenada), float(lat), float(lon))
    )


def _get_pilotos_con_datos(rally_id: str, ss_id: str) -> list[str]:
    """Pilotos que tienen telemetría para ese rally+ss."""
    try:
        rows = cassandra_query(
            "SELECT DISTINCT piloto_id FROM telemetria_auto WHERE rally_id=%s AND ss_id=%s",
            (rally_id, ss_id)
        )
        return [r.piloto_id for r in rows] or ["wrc_ogier_01"]
    except Exception:
        return ["wrc_ogier_01"]


# ─── diálogos ─────────────────────────────────────────────────────────────────

def _dialogo_insertar(rally_id: str, ss_id: str, piloto_id: str, contenedor):
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:560px;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{GREEN};">'
                f'◈  Insertar telemetría</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")
        ui.html(f'<div class="section-label">PARÁMETROS</div>')

        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_rally   = ui.input("rally_id",   value=rally_id).props("outlined dark dense")
            inp_ss      = ui.input("ss_id",      value=ss_id).props("outlined dark dense")
            inp_piloto  = ui.input("piloto_id",  value=piloto_id).props("outlined dark dense")
            inp_vel     = ui.number("Velocidad km/h", value=145.0, format="%.1f").props("outlined dark dense")
            inp_rpm     = ui.number("RPM",        value=6800, format="%.0f").props("outlined dark dense")
            inp_marcha  = ui.number("Marcha",     value=4, format="%.0f").props("outlined dark dense")
            inp_acel    = ui.number("Aceleración %", value=78.5, format="%.1f").props("outlined dark dense")
            inp_freno   = ui.number("Frenada %",  value=0.0, format="%.1f").props("outlined dark dense")
            inp_lat     = ui.number("Latitud",    value=-31.4201, format="%.6f").props("outlined dark dense")
            inp_lon     = ui.number("Longitud",   value=-64.1888, format="%.6f").props("outlined dark dense")

        def insertar():
            try:
                _insertar_muestra(
                    inp_rally.value, inp_ss.value, inp_piloto.value,
                    inp_vel.value, inp_rpm.value, inp_marcha.value,
                    inp_acel.value, inp_freno.value, inp_lat.value, inp_lon.value
                )
                ui.notify("Telemetría insertada ✓", type="positive")
                dlg.close()
                _refrescar_tabla(inp_rally.value, inp_ss.value, inp_piloto.value, contenedor)
            except Exception as e:
                ui.notify(f"Error Cassandra: {e}", type="negative")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            ui.button("Insertar", on_click=insertar).props("unelevated").style(
                f"background:{GREEN}; color:{DARK}; font-family:Courier New; font-weight:bold;"
            )
    dlg.open()


# ─── render tabla telemetría ──────────────────────────────────────────────────

def _refrescar_tabla(rally_id: str, ss_id: str, piloto_id: str, contenedor):
    contenedor.clear()
    filas = _cargar_telemetria(rally_id, ss_id, piloto_id)

    with contenedor:
        if not filas:
            ui.html(
                f'<div style="font-family:Courier New;color:{GREY};padding:16px;">'
                f'Sin telemetría para <b style="color:{GREEN};">{piloto_id}</b> · '
                f'{ss_id}. Insertá una muestra con el botón ◈ o verificá Cassandra.</div>'
            )
            return

        # Si hay error de conexión
        if "error" in filas[0]:
            ui.html(
                f'<div style="font-family:Courier New;padding:12px;">'
                f'<span style="color:{RED};">Error Cassandra:</span> '
                f'<span style="color:{GREY};">{filas[0]["error"]}</span><br><br>'
                f'<span style="color:{GREY};">Verificá que Cassandra esté corriendo y el keyspace '
                f'<b>wrc_telemetria</b> exista con la tabla <b>telemetria_auto</b>.</span></div>'
            )
            return

        columnas = [
            {"name": "timestamp",   "label": "TIMESTAMP",   "field": "timestamp",   "align": "left",   "style": f"color:{GREY}; font-size:0.78rem;"},
            {"name": "velocidad",   "label": "VEL km/h",    "field": "velocidad",   "align": "center", "style": f"color:{GREEN}; font-weight:bold;"},
            {"name": "rpm",         "label": "RPM",         "field": "rpm",         "align": "center", "style": f"color:{GOLD};"},
            {"name": "marcha",      "label": "MARCHA",      "field": "marcha",      "align": "center", "style": f"color:{WHITE};"},
            {"name": "aceleracion", "label": "ACEL %",      "field": "aceleracion", "align": "center", "style": f"color:{GREEN};"},
            {"name": "frenada",     "label": "FRENO %",     "field": "frenada",     "align": "center", "style": f"color:{RED};"},
            {"name": "lat",         "label": "LAT",         "field": "lat",         "align": "center", "style": f"color:{GREY};"},
            {"name": "lon",         "label": "LON",         "field": "lon",         "align": "center", "style": f"color:{GREY};"},
        ]
        ui.table(columns=columnas, rows=filas, row_key="timestamp").style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
        ).props("flat dark")


# ─── página principal ─────────────────────────────────────────────────────────

@ui.page("/realtime/telemetria")
def page_telemetria():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    # Estado de la consulta
    estado = {
        "rally_id":  "rally_arg_2026",
        "ss_id":     "ss_ejemplo_01",
        "piloto_id": "wrc_ogier_01",
    }

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/realtime/telemetria")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):

            # Header
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">TELEMETRÍA</div>')
                    ui.html(
                        f'<div class="wrc-label">Cassandra · keyspace: '
                        f'<span style="color:{GREEN};">wrc_telemetria</span> · '
                        f'tabla: <span style="color:{GREEN};">telemetria_auto</span></div>'
                    )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            # Filtros
            ui.html(f'<div class="section-label">FILTROS</div>')
            with ui.row().classes("items-center gap-3 flex-wrap w-full"):
                inp_rally  = ui.input("rally_id",  value=estado["rally_id"]).props("outlined dark dense").style("min-width:180px;")
                inp_ss     = ui.input("ss_id",     value=estado["ss_id"]).props("outlined dark dense").style("min-width:200px;")
                inp_piloto = ui.input("piloto_id", value=estado["piloto_id"]).props("outlined dark dense").style("min-width:180px;")
                inp_limite = ui.number("Límite filas", value=50, format="%.0f").props("outlined dark dense").style("width:120px;")

            contenedor_tabla = ui.column().classes("w-full")

            def buscar():
                estado["rally_id"]  = inp_rally.value.strip()
                estado["ss_id"]     = inp_ss.value.strip()
                estado["piloto_id"] = inp_piloto.value.strip()
                _refrescar_tabla(estado["rally_id"], estado["ss_id"], estado["piloto_id"], contenedor_tabla)

            with ui.row().classes("gap-2").style("margin:12px 0;"):
                ui.button("🔍  Consultar", on_click=buscar).props("unelevated").style(
                    f"background:{GREEN}; color:{DARK}; font-family:Courier New; font-weight:bold;"
                )
                ui.button(
                    "◈  Insertar muestra",
                    on_click=lambda: _dialogo_insertar(
                        inp_rally.value, inp_ss.value, inp_piloto.value, contenedor_tabla
                    )
                ).props("flat").style(
                    f"color:{GREEN}; font-family:Courier New; border:1px solid {BORDER};"
                )

            # Tabla inicial
            _refrescar_tabla(estado["rally_id"], estado["ss_id"], estado["piloto_id"], contenedor_tabla)

            # Schema Cassandra
            ui.html('<div class="section-label" style="margin-top:20px;">SCHEMA CASSANDRA</div>')
            ui.html(
                '<div class="code-block">'
                'CREATE KEYSPACE wrc_telemetria\n'
                '  WITH replication = {\'class\': \'SimpleStrategy\', \'replication_factor\': 1};\n\n'
                'CREATE TABLE wrc_telemetria.telemetria_auto (\n'
                '  rally_id     TEXT,\n'
                '  ss_id        TEXT,\n'
                '  piloto_id    TEXT,\n'
                '  timestamp    TIMESTAMP,\n'
                '  velocidad    FLOAT,\n'
                '  rpm          INT,\n'
                '  marcha       INT,\n'
                '  aceleracion  FLOAT,\n'
                '  frenada      FLOAT,\n'
                '  lat          DOUBLE,\n'
                '  lon          DOUBLE,\n'
                '  PRIMARY KEY ((rally_id, ss_id, piloto_id), timestamp)\n'
                ') WITH CLUSTERING ORDER BY (timestamp DESC);\n\n'
                '// ss_id comparte valor con MongoDB: rallies.legs.special_stages.ss_id\n'
                '// piloto_id comparte valor con Redis: ZADD timing:{rally_id}:{ss_id}'
                '</div>'
            )
