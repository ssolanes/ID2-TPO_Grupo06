# frontend_static/pages/jefes_ingenieria.py
# CRUD completo de jefes de ingeniería · MongoDB

from nicegui import ui
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    generar_mongo_id, sync_neo_node_from_doc, delete_neo_node_from_doc,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc: dict) -> dict:
    certificados = doc.get("certificaciones", [])
    return {
        "_id":          str(doc.get("_id", "")),
        "nombre":       f'{doc.get("nombre","")} {doc.get("apellido","")}',
        "especialidad": doc.get("especialidad", "—"),
        "email":        doc.get("email", "—"),
        "telefono":     doc.get("telefono", "—"),
        "certificaciones": ", ".join(certificados) if isinstance(certificados, list) else str(certificados),
    }


def _cargar_filas():
    try:
        col = mongo_col("jefe_ingenieria")
        return [_doc_a_fila(d) for d in col.find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _dialogo_jefe(tabla, doc_id: str = None):
    col = mongo_col("jefe_ingenieria")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:560px; max-height:80vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">'
                f'{"✏  Editar Jefe de Ingeniería" if doc_id else "＋  Nuevo Jefe de Ingeniería"}</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        lbl("DATOS PERSONALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_nombre   = ui.input("Nombre",   value=doc.get("nombre", "")).props("outlined dark dense")
            inp_apellido = ui.input("Apellido", value=doc.get("apellido", "")).props("outlined dark dense")
            inp_esp      = ui.input("Especialidad", value=doc.get("especialidad", "")).props("outlined dark dense")

        lbl("CONTACTO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_email    = ui.input("Email",       value=doc.get("email", "")).props("outlined dark dense")
            inp_tel      = ui.input("Teléfono",    value=doc.get("telefono", "")).props("outlined dark dense")

        lbl("CERTIFICACIONES")
        inp_certs = ui.input(
            "Certificaciones (separadas por coma)",
            value=", ".join(doc.get("certificaciones", [])) if isinstance(doc.get("certificaciones"), list) else ""
        ).props("outlined dark dense").classes("w-full")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            certs_list = [c.strip() for c in inp_certs.value.split(",") if c.strip()]
            
            nuevo = {
                "nombre":           inp_nombre.value.strip(),
                "apellido":         inp_apellido.value.strip(),
                "especialidad":     inp_esp.value.strip(),
                "email":            inp_email.value.strip(),
                "telefono":         inp_tel.value.strip(),
                "certificaciones":  certs_list,
            }

            try:
                if doc_id:
                    col.update_one(
                        {"_id": get_query_id(doc_id)},
                        {"$set": nuevo, "$unset": {
                            "estado": "",
                            "equipo_id": "",
                            "años_experiencia": "",
                        }},
                    )
                    sync_neo_node_from_doc("JefeIngenieria", doc_id)
                    ui.notify("Jefe de ingeniería actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    nuevo["_id"] = generar_mongo_id("jefe_ingenieria", "jefe", nuevo["nombre"], nuevo["apellido"])
                    result = col.insert_one(nuevo)
                    sync_neo_node_from_doc("JefeIngenieria", str(result.inserted_id))
                    ui.notify("Jefe de ingeniería creado en MongoDB y Neo4j ✓", type="positive")
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
    col = mongo_col("jefe_ingenieria")
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};font-size:1rem;">'
                f'¿Eliminar a <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    delete_neo_node_from_doc("JefeIngenieria", doc_id)
                    ui.notify("Jefe de ingeniería eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/jefes_ingenieria")
def page_jefes_ingenieria():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/jefes_ingenieria")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">JEFES DE INGENIERÍA</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">jefe_ingenieria</span></div>')
                ui.button("＋  Nuevo jefe",
                          on_click=lambda: _dialogo_jefe(tabla)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "nombre",       "label": "INGENIERO",   "field": "nombre",       "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "especialidad", "label": "ESPECIALIDAD","field": "especialidad", "sortable": True,  "align": "left",   "style": f"color:{BLUE};"},
                {"name": "email",        "label": "EMAIL",       "field": "email",        "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "telefono",     "label": "TELÉFONO",    "field": "telefono",     "sortable": False, "align": "left",   "style": f"color:{GREY};"},
                {"name": "certificaciones","label": "CERTIFICACIONES","field": "certificaciones","sortable": False,"align": "left", "style": f"color:{GREY}; font-size:0.8rem;"},
                {"name": "acciones",     "label": "ACCIONES",    "field": "acciones",     "sortable": False, "align": "center"},
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

            tabla.on("editar",   lambda e: _dialogo_jefe(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("nombre", "?")))
