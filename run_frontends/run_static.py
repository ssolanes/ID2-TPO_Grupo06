# run_static.py
# Frontend estático: MongoDB + Neo4j (CRUD)

from nicegui import ui
import frontend_static.pages.pilotos            # type: ignore
import frontend_static.pages.copilotos          # type: ignore
import frontend_static.pages.jefes_ingenieria   # type: ignore
import frontend_static.pages.equipos            # type: ignore
import frontend_static.pages.vehiculos          # type: ignore
import frontend_static.pages.patrocinadores     # type: ignore
import frontend_static.pages.rallies            # type: ignore
import frontend_static.pages.resumenes_carrera  # type: ignore
import frontend_static.pages.noticias_reportes  # type: ignore
import frontend_static.pages.neo4j_relaciones   # type: ignore

@ui.page("/")
def index():
    from frontend_static.shared import GLOBAL_CSS, DARK, RED, BLUE, GREY, CARD, BORDER, GREEN
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.column().classes("items-center justify-center").style(
        f"min-height:100vh; width:100%;"
    ):
        ui.html(
            f'<div style="text-align:center; padding:40px;">'
            f'<div style="font-family:Courier New; font-size:3rem; font-weight:bold; color:{RED};">WRC</div>'
            f'<div style="font-family:Courier New; font-size:1rem; color:{GREY}; margin-bottom:32px;">'
            f'Static Data Management · MongoDB + Neo4j</div>'
            f'</div>'
        )
        with ui.row().classes("gap-4 flex-wrap justify-center").style("max-width:900px;"):
            for ruta, label, color in [
                ("/static/pilotos",           "◉  Pilotos",             RED),
                ("/static/copilotos",         "○  Copilotos",           RED),
                ("/static/jefes_ingenieria",  "⚙  Jefes Ingeniería",    RED),
                ("/static/equipos",           "◈  Equipos",             RED),
                ("/static/vehiculos",         "⛍  Vehículos",           RED),
                ("/static/patrocinadores",    "◇  Patrocinadores",      RED),
                ("/static/rallies",           "◎  Rallies / Etapas",    RED),
                ("/static/resumenes_carrera", "🏁 Resúmenes Carrera",    RED),
                ("/static/noticias_reportes", "📰 Noticias / Reportes",  RED),
                ("/static/neo4j",             "⬡  Neo4j · Relaciones",   BLUE),
            ]:
                ui.html(
                    f'<a href="{ruta}" style="display:block; padding:16px 28px; '
                    f'background:{CARD}; border:1px solid {BORDER}; border-radius:10px; '
                    f'font-family:Courier New; font-weight:bold; color:{color}; '
                    f'text-decoration:none; font-size:1rem; min-width:260px; text-align:center;">'
                    f'{label}</a>'
                )

ui.run(
    host="0.0.0.0",
    port=8081,
    title="WRC Static · MongoDB + Neo4j",
    reload=False,
    show=False,
)