# run_static.py
# Levanta el frontend estático: MongoDB + Neo4j (CRUD)

from nicegui import ui
import frontend_static.pages.pilotos
import frontend_static.pages.equipos
import frontend_static.pages.rallies
import frontend_static.pages.patrocinadores
import frontend_static.pages.neo4j_relaciones  # registra todas las rutas

@ui.page("/")
def index():
    from nicegui import ui
    from frontend_static.shared import GLOBAL_CSS, DARK, RED, GOLD, GREY, CARD, CARD2, BORDER, WHITE, GREEN, BLUE
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.column().classes("items-center justify-center").style(
        f"min-height:100vh; background:{DARK}; width:100%;"
    ):
        ui.html(
            f'<div style="text-align:center; padding:40px;">'
            f'<div style="font-family:Courier New; font-size:3rem; font-weight:bold; color:{RED};">WRC</div>'
            f'<div style="font-family:Courier New; font-size:1rem; color:{GREY}; margin-bottom:32px;">'
            f'Static Data Management · MongoDB + Neo4j</div>'
            f'</div>'
        )
        with ui.row().classes("gap-4 flex-wrap justify-center"):
            for ruta, label, color in [
                ("/static/pilotos",        "◉  Pilotos",         RED),
                ("/static/equipos",        "◈  Equipos",         RED),
                ("/static/rallies",        "◎  Rallies / Etapas",RED),
                ("/static/patrocinadores", "◇  Patrocinadores",  RED),
                ("/static/neo4j",          "⬡  Neo4j · Relaciones", BLUE),
            ]:
                ui.html(
                    f'<a href="{ruta}" style="display:block; padding:16px 28px; '
                    f'background:{CARD}; border:1px solid {BORDER}; border-radius:10px; '
                    f'font-family:Courier New; font-weight:bold; color:{color}; '
                    f'text-decoration:none; font-size:1rem; min-width:220px; text-align:center;">'
                    f'{label}</a>'
                )

ui.run(
    host="0.0.0.0",
    port=8081,
    title="WRC Static · MongoDB + Neo4j",
    reload=False,
    show=False,
)
