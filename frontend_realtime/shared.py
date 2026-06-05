# frontend_realtime/shared.py
# Conexiones a Redis y Cassandra + estilos compartidos (tiempo real)

import redis
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# ─── Redis ───────────────────────────────────────────────────────────────────
_redis_client = None

def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
        )
    return _redis_client


# ─── Cassandra ────────────────────────────────────────────────────────────────
_cassandra_session = None

def get_cassandra():
    global _cassandra_session
    if _cassandra_session is None:
        cluster = Cluster(
            ["127.0.0.1"],
            port=9042,
            # auth_provider=PlainTextAuthProvider("cassandra", "cassandra"),  # descomentá si usás auth
        )
        _cassandra_session = cluster.connect("wrc_telemetria")  # keyspace
    return _cassandra_session

def cassandra_query(cql: str, params: tuple = None):
    session = get_cassandra()
    result = session.execute(cql, params or ())
    return list(result)


# ─── Paleta WRC (misma que static) ───────────────────────────────────────────
RED    = "#E8002A"
GOLD   = "#F5C518"
BLUE   = "#0080FF"
GREEN  = "#00D97E"
DARK   = "#0A0A0C"
PANEL  = "#111116"
CARD   = "#16161D"
CARD2  = "#1C1C24"
WHITE  = "#F0F0F0"
GREY   = "#8A8A9A"
BORDER = "#2A2A38"

GLOBAL_CSS = f"""
<style>
  body, .nicegui-content {{ background: {DARK} !important; }}
  .wrc-title {{
    font-family: 'Courier New', monospace;
    font-weight: bold; color: {WHITE};
  }}
  .wrc-label {{
    font-family: 'Courier New', monospace;
    color: {GREY}; font-size: 0.85rem;
  }}
  .section-label {{
    font-family: 'Courier New', monospace;
    font-size: 0.75rem; font-weight: bold;
    color: {RED}; letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 16px 0 8px 0;
  }}
  .code-block {{
    background: {CARD2}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 14px;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem; color: {GREEN};
    white-space: pre; overflow-x: auto;
  }}
  .badge-green {{
    background: #002918; border: 1px solid #004D2E;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {GREEN};
  }}
  .badge-red {{
    background: #2D0009; border: 1px solid #4A000F;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {RED};
  }}
  .badge-gold {{
    background: #2D2400; border: 1px solid #4A3A00;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {GOLD};
  }}
  .badge-blue {{
    background: #001A33; border: 1px solid #003366;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {BLUE};
  }}
  .nav-link {{
    font-family: 'Courier New', monospace;
    color: {GREY}; text-decoration: none;
    padding: 8px 16px; border-radius: 6px;
    transition: background 0.2s;
  }}
  .nav-link:hover {{ background: {CARD2}; color: {WHITE}; }}
  .nav-active {{
    background: {CARD2}; color: {WHITE} !important;
    border-left: 3px solid {GOLD};
  }}
  .live-dot {{
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: {RED};
    animation: blink 1s infinite;
    margin-right: 6px;
  }}
  @keyframes blink {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.2; }}
  }}
  .q-table {{ background: {CARD} !important; }}
  .q-table thead tr {{ background: {CARD2} !important; }}
  .q-table tbody tr:hover {{ background: {CARD2} !important; }}
  .q-table th, .q-table td {{
    font-family: 'Courier New', monospace !important;
    color: {WHITE} !important;
    border-color: {BORDER} !important;
  }}
</style>
"""


def sidebar(pagina_actual: str):
    """Barra lateral de navegación del frontend realtime."""
    from nicegui import ui

    items = [
        ("/realtime/live_timing",  "⬤  Live Timing"),
        ("/realtime/telemetria",   "◈  Telemetría"),
    ]

    with ui.column().classes("h-full").style(
        f"width:220px; min-height:100vh; background:{PANEL}; "
        f"border-right:1px solid {BORDER}; padding:0; flex-shrink:0;"
    ):
        with ui.element("div").style(
            f"background:{CARD2}; padding:18px 16px; border-bottom:1px solid {BORDER};"
        ):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.6rem;font-weight:bold;color:{RED};">WRC</span>'
                f'<span style="font-family:Courier New;font-size:0.75rem;color:{GREY};display:block;margin-top:2px;">'
                f'Realtime · <span style="color:{GOLD};">Redis + Cassandra</span></span>'
            )

        ui.separator().style(f"background:{BORDER}; margin:0;")
        ui.html(f'<div class="section-label" style="padding:0 16px;">Tiempo real</div>')

        for ruta, label in items:
            activo = pagina_actual == ruta
            clase = "nav-link nav-active" if activo else "nav-link"
            ui.html(
                f'<a href="{ruta}" class="{clase}" '
                f'style="display:block; margin:2px 8px;">{label}</a>'
            )

        with ui.element("div").style(
            f"position:absolute; bottom:0; width:220px; padding:12px 16px; "
            f"border-top:1px solid {BORDER}; background:{PANEL};"
        ):
            ui.html(
                f'<div style="font-family:Courier New;font-size:0.7rem;color:{GREY};text-align:center;">'
                f'FIA · Temporada 2026<br>'
                f'<span style="color:{BORDER};">Redis · Cassandra</span></div>'
            )
