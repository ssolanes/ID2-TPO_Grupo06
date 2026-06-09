from nicegui import ui
from frontend_static.shared import GLOBAL_CSS, DARK, RED, BLUE, GREY, CARD, BORDER, GREEN

@ui.page("/")
def index():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK}; margin:0; padding:24px; box-sizing:border-box;")

    # Botón
    ui.button("Iniciar carrera ▷").style(
        f"background:{GREEN}; color:{DARK}; font-family:'Courier New',monospace; "
        f"font-weight:bold; font-size:1rem; border-radius:8px; padding:14px 28px;"
    )

    # Fila superior
    with ui.row().style(f"width:100%; gap:16px; margin-top:20px; height:380px; flex-wrap:nowrap;"):
        with ui.card().style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
            f"flex:2; height:100%; padding:20px; box-shadow:none;"
        ):
            ui.label("Video").style(f"font-family:'Courier New',monospace; color:#f0f0f0; font-size:0.9rem;")

        with ui.card().style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
            f"flex:1; height:100%; padding:20px; box-shadow:none;"
        ):
            ui.label("Datos Redis").style(f"font-family:'Courier New',monospace; color:#f0f0f0; font-size:0.9rem;")

        with ui.card().style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
            f"flex:1; height:100%; padding:20px; box-shadow:none;"
        ):
            ui.label("Datos Redis").style(f"font-family:'Courier New',monospace; color:#f0f0f0; font-size:0.9rem;")

    # Fila inferior
    with ui.card().style(
        f"background:{CARD}; border:1px solid {BORDER}; border-radius:12px; "
        f"width:100%; min-height:200px; margin-top:16px; padding:20px; box-shadow:none;"
    ):
        ui.label("Datos Cassandra").style(f"font-family:'Courier New',monospace; color:#f0f0f0; font-size:0.9rem;")


ui.run(
    host="0.0.0.0",
    port=8082,
    title="WRC Realtime · Redis + Cassandra",
    reload=False,
    show=False,
)