# frontend_static/pages/pilotos.py
# CRUD completo de pilotos · MongoDB

from nicegui import ui
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    sync_neo_node_from_doc, delete_neo_node_from_doc,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _col(nombre):
    return mongo_col("pilotos")


# ─── Helpers ────────────────────────────────────────────────────────────────

def _doc_a_fila(doc: dict) -> dict:
    return {
        "_id":       str(doc.get("_id", "")),
        "nombre":    f'{doc.get("nombre","")} {doc.get("apellido","")}',
        "pais":      doc.get("pais", {}).get("nombre", "—") if isinstance(doc.get("pais"), dict) else doc.get("pais", "—"),
    }


def _cargar_filas():
    try:
        col = mongo_col("pilotos")
        return [_doc_a_fila(d) for d in col.find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _nombre_completo(doc: dict) -> str:
    return f'{doc.get("nombre", "")} {doc.get("apellido", "")}'.strip()


# ─── Dialogo CREAR / EDITAR ──────────────────────────────────────────────────

def _dialogo_piloto(tabla, doc_id: str = None):
    col = mongo_col("pilotos")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

    pais  = doc.get("pais", {})

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:560px; max-height:80vh; overflow-y:auto;"):

        # Header
        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">'
                f'{"✏  Editar Piloto" if doc_id else "＋  Nuevo Piloto"}</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        # Formulario
        lbl("DATOS PERSONALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_nombre   = ui.input("Nombre",   value=doc.get("nombre", "")).props("outlined dark dense").style(f"color:{WHITE};")
            inp_apellido = ui.input("Apellido", value=doc.get("apellido", "")).props("outlined dark dense")
            inp_pais     = ui.input("País",     value=pais.get("nombre", "") if isinstance(pais, dict) else str(pais)).props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            nuevo = {
                "nombre":      inp_nombre.value.strip(),
                "apellido":    inp_apellido.value.strip(),
                "pais":        {"nombre": inp_pais.value.strip()},
            }
            try:
                if doc_id:
                    col.update_one(
                        {"_id": get_query_id(doc_id)},
                        {"$set": nuevo, "$unset": {
                            "estadisticas": "",
                            "estado": "",
                            "fecha_nacimiento": "",
                            "equipo_id": "",
                            "copiloto_id": "",
                            "vehiculo_id": "",
                            "numero_auto": "",
                            "sponsors": "",
                        }},
                    )
                    sync_neo_node_from_doc("Piloto", doc_id)
                    ui.notify("Piloto actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    result = col.insert_one(nuevo)
                    sync_neo_node_from_doc("Piloto", str(result.inserted_id))
                    ui.notify("Piloto creado en MongoDB y Neo4j ✓", type="positive")
                dlg.close()
                tabla.rows = _cargar_filas()
                tabla.update()
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            ui.button("Guardar", on_click=guardar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
            )

    dlg.open()


def _confirmar_eliminar(tabla, doc_id: str, nombre: str):
    col = mongo_col("pilotos")
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};font-size:1rem;">'
                f'¿Eliminar a <b style="color:{RED};">{nombre}</b>?</div>')
        ui.html(f'<div style="font-family:Courier New;color:{GREY};font-size:0.85rem;margin-top:6px;">'
                f'Esta acción no se puede deshacer.</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    delete_neo_node_from_doc("Piloto", doc_id)
                    ui.notify("Piloto eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


# ─── Página principal ────────────────────────────────────────────────────────

@ui.page("/static/pilotos")
def page_pilotos():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/pilotos")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            # Header
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">PILOTOS</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">pilotos</span></div>')
                ui.button("＋  Nuevo piloto",
                          on_click=lambda: _dialogo_piloto(tabla)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            # Tabla
            columnas = [
                {"name": "nombre",    "label": "PILOTO",    "field": "nombre",    "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "pais",      "label": "PAÍS",      "field": "pais",      "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "acciones",  "label": "ACCIONES",  "field": "acciones",  "sortable": False, "align": "center"},
            ]

            filas = _cargar_filas()

            tabla = ui.table(columns=columnas, rows=filas, row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-acciones", """
                <q-td :props="props" style="text-align:center;">
                  <q-btn flat round dense icon="edit"
                    style="color:#F5C518; margin-right:4px;"
                    @click="$parent.$emit('editar', props.row)" />
                  <q-btn flat round dense icon="delete"
                    style="color:#E8002A;"
                    @click="$parent.$emit('eliminar', props.row)" />
                </q-td>
            """)

            tabla.on("editar",   lambda e: _dialogo_piloto(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("nombre", "?")))
