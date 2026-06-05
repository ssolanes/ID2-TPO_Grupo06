# run_realtime.py
# Levanta el frontend de tiempo real: Redis + Cassandra

from nicegui import ui
import frontend_realtime.pages.live_timing
import frontend_realtime.pages.telemetria  # registra todas las rutas

@ui.page("/")
def index():
    from nicegui import ui
    from frontend_realtime.shared import GLOBAL_CSS, DARK, RED, GOLD, GREY, CARD, BORDER, WHITE, GREEN, BLUE
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.column().classes("items-center justify-center").style(
        f"min-height:100vh; background:{DARK}; width:100%;"
    ):
        ui.html(
            f'<div style="text-align:center; padding:40px;">'
            f'<div style="font-family:Courier New; font-size:3rem; font-weight:bold; color:{RED};">WRC</div>'
            f'<div style="font-family:Courier New; font-size:1rem; color:{GREY}; margin-bottom:8px;">'
            f'Realtime · Redis + Cassandra</div>'
            f'<span style="display:inline-block; width:8px; height:8px; border-radius:50%; '
            f'background:{RED}; animation:blink 1s infinite; margin-right:6px;"></span>'
            f'<span style="font-family:Courier New; font-size:0.85rem; color:{RED};">EN VIVO</span>'
            f'</div>'
        )
        with ui.row().classes("gap-4 flex-wrap justify-center"):
            for ruta, label, color in [
                ("/realtime/live_timing", "⬤  Live Timing · Redis", RED),
                ("/realtime/telemetria",  "◈  Telemetría · Cassandra", GREEN),
            ]:
                ui.html(
                    f'<a href="{ruta}" style="display:block; padding:16px 28px; '
                    f'background:#16161D; border:1px solid #2A2A38; border-radius:10px; '
                    f'font-family:Courier New; font-weight:bold; color:{color}; '
                    f'text-decoration:none; font-size:1rem; min-width:240px; text-align:center;">'
                    f'{label}</a>'
                )

ui.run(
    host="0.0.0.0",
    port=8082,
    title="WRC Realtime · Redis + Cassandra",
    reload=False,
    show=False,
)
