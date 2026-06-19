# frontend_static/pages/vehiculos.py
# CRUD completo de vehículos · MongoDB

from nicegui import ui
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    sync_neo_node_from_doc, delete_neo_node_from_doc, mostrar_dialogo_relaciones,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL,
    TablaPaginada
)


def _doc_a_fila(doc: dict) -> dict:
    config = doc.get("configuracion", {})
    traccion = config.get("traccion", "—")
    mecanico = doc.get("estado_mecanico", {})
    ok = bool(mecanico.get("ok", True))

    return {
        "_id":         str(doc.get("_id", "")),
        "modelo":      f'{doc.get("marca","")} {doc.get("modelo","")}',
        "anio":        doc.get("anio", "—"),
        "combustible": doc.get("tipo_combustible", "—"),
        "traccion":    traccion,
        "ok":          ok,
        "estado_mec":  "OK" if ok else "Con falla",
    }


def _cargar_filas():
    try:
        col = mongo_col("vehiculos")
        return [_doc_a_fila(d) for d in col.find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _dialogo_vehiculo(tabla, doc_id: str = None):
    col = mongo_col("vehiculos")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

    config = doc.get("configuracion", {})
    mecanico = doc.get("estado_mecanico", {})

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:560px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">'
                f'{"✏  Editar Vehículo" if doc_id else "＋  Nuevo Vehículo"}</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        lbl("DATOS GENERALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_marca    = ui.input("Marca",  value=doc.get("marca", "")).props("outlined dark dense")
            inp_modelo   = ui.input("Modelo", value=doc.get("modelo", "")).props("outlined dark dense")
            inp_anio     = ui.number("Año",   value=doc.get("anio", 2026), format="%.0f").props("outlined dark dense")
            inp_combust  = ui.select(["hibrido", "nafta", "diesel", "electrico"], value=doc.get("tipo_combustible", "hibrido"), label="Combustible").props("outlined dark dense")
            inp_traccion = ui.input("Tracción (ej: 4WD)", value=config.get("traccion", "4WD")).props("outlined dark dense")
            inp_estado   = ui.select(["ok", "con falla"], value="ok" if mecanico.get("ok", True) else "con falla", label="Estado mecánico").props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            ok = inp_estado.value == "ok"
            nuevo = {
                "marca":            inp_marca.value.strip(),
                "modelo":           inp_modelo.value.strip(),
                "anio":             int(inp_anio.value or 0),
                "tipo_combustible": inp_combust.value,
                "configuracion": {
                    "traccion":    inp_traccion.value.strip(),
                },
                "estado_mecanico": {
                    "ok": ok,
                    "falla_activa": None if ok else {"tipo": "General", "gravedad": "Media"},
                }
            }

            try:
                if doc_id:
                    col.update_one(
                        {"_id": get_query_id(doc_id)},
                        {"$set": nuevo, "$unset": {
                            "equipo_id": "",
                            "motor": "",
                            "configuracion.transmision": "",
                            "configuracion.suspension": "",
                            "estado_mecanico.ultima_revision": "",
                        }},
                    )
                    sync_neo_node_from_doc("Vehiculo", doc_id)
                    ui.notify("Vehículo actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    result = col.insert_one(nuevo)
                    sync_neo_node_from_doc("Vehiculo", str(result.inserted_id))
                    ui.notify("Vehículo creado en MongoDB y Neo4j ✓", type="positive")
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
    col = mongo_col("vehiculos")
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};font-size:1rem;">'
                f'¿Eliminar vehículo <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    delete_neo_node_from_doc("Vehiculo", doc_id)
                    ui.notify("Vehículo eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/vehiculos")
def page_vehiculos():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/vehiculos")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">VEHÍCULOS</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">vehiculos</span></div>')
                ui.button("＋  Nuevo vehículo",
                          on_click=lambda: _dialogo_vehiculo(tabla)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "modelo",     "label": "VEHÍCULO",    "field": "modelo",      "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "anio",       "label": "AÑO",         "field": "anio",        "sortable": True,  "align": "center", "style": f"color:{GREY};"},
                {"name": "combustible","label": "COMBUSTIBLE", "field": "combustible", "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "traccion",   "label": "TRACCIÓN",    "field": "traccion",    "sortable": True,  "align": "center", "style": f"color:{GREY};"},
                {"name": "estado_mec", "label": "ESTADO MECÁNICO", "field": "estado_mec", "sortable": True, "align": "center"},
                {"name": "acciones",   "label": "ACCIONES",    "field": "acciones",    "sortable": False, "align": "center"},
            ]

            filas = _cargar_filas()

            tabla = TablaPaginada(columns=columnas, rows=filas, row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-estado_mec", """
                <q-td :props="props">
                  <span :class="props.row.ok ? 'badge-green' : 'badge-red'">
                    {{ props.value.toUpperCase() }}
                  </span>
                </q-td>
            """)

            tabla.add_slot("body-cell-acciones", """
                <q-td :props="props" style="text-align:center;">
                  <q-btn flat round dense icon="link"
                    style="color:#0080FF; margin-right:4px;"
                    @click="$parent.$emit('relaciones', props.row)" />
                  <q-btn flat round dense icon="edit"
                    style="color:#F5C518; margin-right:4px;"
                    @click="$parent.$emit('editar', props.row)" />
                  <q-btn flat round dense icon="delete"
                    style="color:#E8002A;"
                    @click="$parent.$emit('eliminar', props.row)" />
                </q-td>
            """)

            tabla.on("relaciones", lambda e: mostrar_dialogo_relaciones("Vehiculo", e.args.get("_id"), e.args.get("modelo", "?")))
            tabla.on("editar",   lambda e: _dialogo_vehiculo(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("modelo", "?")))
