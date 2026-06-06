# run.py
# Levanta run_static.py (8081) y run_realtime.py (8082) en paralelo
# y abre el selector en el navegador automáticamente (8080).

import subprocess
import sys
import os
import threading
import time
from nicegui import ui

# ─── Arrancar los otros 2 servidores en background ───────────────────────────

def _lanzar(script: str):
    base = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(base, script)
    env = os.environ.copy()
    env["PYTHONPATH"] = base
    subprocess.Popen(
        [sys.executable, ruta],
        cwd=base,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def _lanzar_servidores():
    time.sleep(1)
    _lanzar("./run_frontends/run_static.py")
    _lanzar("./run_frontends/run_realtime.py")

threading.Thread(target=_lanzar_servidores, daemon=True).start()

# ─── Estilos ──────────────────────────────────────────────────────────────────

RED    = "#E8002A"
GOLD   = "#F5C518"
GREEN  = "#00D97E"
BLUE   = "#0080FF"
DARK   = "#0A0A0C"
CARD   = "#16161D"
CARD2  = "#1C1C24"
GREY   = "#8A8A9A"
BORDER = "#2A2A38"
WHITE  = "#F0F0F0"

GLOBAL_CSS = f"""
<style>
  body {{ background: {DARK} !important; margin: 0; }}
  @keyframes blink {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.2; }}
  }}
  .option-card {{
    display: block;
    padding: 32px 40px;
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 14px;
    text-decoration: none;
    min-width: 280px;
    text-align: center;
    transition: border-color 0.2s, background 0.2s;
    cursor: pointer;
  }}
  .option-card:hover {{
    background: {CARD2};
    border-color: #444;
  }}
</style>
"""

# ─── Página selector ─────────────────────────────────────────────────────────

@ui.page("/")
def index():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.column().classes("items-center justify-center").style(
        "min-height:100vh; width:100%; gap:0;"
    ):
        ui.html(
            f'<div style="text-align:center; margin-bottom:48px;">'
            f'<div style="font-family:Courier New; font-size:4rem; font-weight:bold; '
            f'color:{RED}; letter-spacing:0.1em;">WRC</div>'
            f'<div style="font-family:Courier New; font-size:0.9rem; color:{GREY}; '
            f'letter-spacing:0.15em; margin-top:4px;">FIA WORLD RALLY CHAMPIONSHIP · 2026</div>'
            f'</div>'
        )

        ui.html(
            f'<div style="font-family:Courier New; font-size:0.78rem; font-weight:bold; '
            f'color:{RED}; letter-spacing:0.15em; margin-bottom:24px;">SELECCIONÁ UN MÓDULO</div>'
        )

        with ui.row().classes("gap-6 flex-wrap justify-center"):

            # ── Estático ──
            ui.html(
                f'<a href="http://localhost:8081" target="_blank" class="option-card">'
                f'<div style="font-family:Courier New; font-size:2rem; color:{RED}; '
                f'font-weight:bold; margin-bottom:12px;">◈</div>'
                f'<div style="font-family:Courier New; font-size:1.1rem; font-weight:bold; '
                f'color:{WHITE}; margin-bottom:8px;">DATOS ESTÁTICOS</div>'
                f'<div style="font-family:Courier New; font-size:0.8rem; color:{GREY}; '
                f'margin-bottom:16px;">MongoDB · Neo4j</div>'
                f'<div style="font-family:Courier New; font-size:0.75rem; color:{GREY}; '
                f'line-height:1.8;">'
                f'◉ Pilotos<br>◈ Equipos<br>◎ Rallies / Etapas<br>'
                f'◇ Patrocinadores<br>⬡ Neo4j · Relaciones'
                f'</div>'
                f'<div style="margin-top:20px; font-family:Courier New; font-size:0.72rem; '
                f'color:{BORDER};">localhost:8081</div>'
                f'</a>'
            )

            # ── Tiempo real ──
            ui.html(
                f'<a href="http://localhost:8082" target="_blank" class="option-card">'
                f'<div style="font-family:Courier New; font-size:2rem; color:{RED}; '
                f'font-weight:bold; margin-bottom:12px;">'
                f'<span style="display:inline-block; width:10px; height:10px; '
                f'border-radius:50%; background:{RED}; '
                f'animation:blink 1s infinite; margin-right:6px; vertical-align:middle;"></span>'
                f'⬤</div>'
                f'<div style="font-family:Courier New; font-size:1.1rem; font-weight:bold; '
                f'color:{WHITE}; margin-bottom:8px;">TIEMPO REAL</div>'
                f'<div style="font-family:Courier New; font-size:0.8rem; color:{GREY}; '
                f'margin-bottom:16px;">Redis · Cassandra</div>'
                f'<div style="font-family:Courier New; font-size:0.75rem; color:{GREY}; '
                f'line-height:1.8;">'
                f'⬤ Live Timing<br>◈ Telemetría'
                f'</div>'
                f'<div style="margin-top:20px; font-family:Courier New; font-size:0.72rem; '
                f'color:{BORDER};">localhost:8082</div>'
                f'</a>'
            )

        ui.html(
            f'<div style="font-family:Courier New; font-size:0.72rem; color:{BORDER}; '
            f'text-align:center; margin-top:48px;">'
            f'Los servidores se están iniciando en background...'
            f'</div>'
        )

ui.run(
    host="0.0.0.0",
    port=8080,
    title="WRC · Selector",
    reload=False,
    show=True,
)