# frontend_static/pages/equipos.py
# CRUD completo de equipos · MongoDB

from nicegui import ui
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    generar_mongo_id, sync_neo_node_from_doc, delete_neo_node_from_doc, mostrar_dialogo_relaciones,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc):
    return {
        "_id":             str(doc.get("_id", "")),
        "nombre":          doc.get("nombre", "—"),
        "pais_base":       doc.get("pais_base", "—"),
        "director":        doc.get("director", "—"),
    }


def _cargar_filas():
    try:
        return [_doc_a_fila(d) for d in mongo_col("equipos").find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _dialogo_equipo(tabla, doc_id=None):
    col = mongo_col("equipos")
    doc = col.find_one({"_id": get_query_id(doc_id)}) if doc_id else {}

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:540px; max-height:80vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{RED};">'
                    f'{"✏  Editar Equipo" if doc_id else "＋  Nuevo Equipo"}</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(t): ui.html(f'<div class="section-label">{t}</div>')

        lbl("DATOS DEL EQUIPO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_nombre    = ui.input("Nombre del equipo", value=doc.get("nombre", "")).props("outlined dark dense")
            inp_pais      = ui.input("País base",         value=doc.get("pais_base", "")).props("outlined dark dense")
            inp_director  = ui.input("Director",          value=doc.get("director", "")).props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            nuevo = {
                "nombre":              inp_nombre.value.strip(),
                "pais_base":           inp_pais.value.strip(),
                "director":            inp_director.value.strip(),
            }
            try:
                if doc_id:
                    col.update_one(
                        {"_id": get_query_id(doc_id)},
                        {"$set": nuevo, "$unset": {
                            "activo": "",
                            "jefe_ingenieria_id": "",
                            "pilotos_ids": "",
                            "copilotos_ids": "",
                            "vehiculos_ids": "",
                            "patrocinadores_ids": "",
                        }},
                    )
                    sync_neo_node_from_doc("Equipo", doc_id)
                    ui.notify("Equipo actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    nuevo["_id"] = generar_mongo_id("equipos", "equipo", nuevo["nombre"])
                    result = col.insert_one(nuevo)
                    sync_neo_node_from_doc("Equipo", str(result.inserted_id))
                    ui.notify("Equipo creado en MongoDB y Neo4j ✓", type="positive")
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


def _confirmar_eliminar(tabla, doc_id, nombre):
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};">¿Eliminar equipo <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    mongo_col("equipos").delete_one({"_id": get_query_id(doc_id)})
                    delete_neo_node_from_doc("Equipo", doc_id)
                    ui.notify("Equipo eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/equipos")
def page_equipos():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/equipos")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">EQUIPOS</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">equipos</span></div>')
                ui.button("＋  Nuevo equipo", on_click=lambda: _dialogo_equipo(tabla)).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "nombre",          "label": "EQUIPO",          "field": "nombre",          "sortable": True, "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "pais_base",       "label": "PAÍS BASE",       "field": "pais_base",       "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "director",        "label": "DIRECTOR",        "field": "director",        "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "acciones",        "label": "ACCIONES",        "field": "acciones",        "sortable": False,"align": "center"},
            ]

            tabla = ui.table(columns=columnas, rows=_cargar_filas(), row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-acciones", """
                <q-td :props="props" style="text-align:center;">
                  <q-btn flat round dense icon="link"   style="color:#0080FF; margin-right:4px;"
                    @click="$parent.$emit('relaciones', props.row)" />
                  <q-btn flat round dense icon="edit"   style="color:#F5C518; margin-right:4px;"
                    @click="$parent.$emit('editar', props.row)" />
                  <q-btn flat round dense icon="delete" style="color:#E8002A;"
                    @click="$parent.$emit('eliminar', props.row)" />
                </q-td>
            """)
            tabla.on("relaciones", lambda e: mostrar_dialogo_relaciones("Equipo", e.args.get("_id"), e.args.get("nombre", "?")))
            tabla.on("editar",   lambda e: _dialogo_equipo(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(tabla, e.args.get("_id"), e.args.get("nombre", "?")))
