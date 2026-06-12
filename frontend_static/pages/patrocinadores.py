# frontend_static/pages/patrocinadores.py
# CRUD de patrocinadores · MongoDB

from nicegui import ui
from bson import ObjectId
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK
)


def _doc_a_fila(doc):
    return {
        "_id":         str(doc.get("_id", "")),
        "nombre":      doc.get("nombre", "—"),
        "tipo":        doc.get("tipo", "—"),
        "pais_origen": doc.get("pais_origen", "—"),
        "activo":      "Activo" if doc.get("activo", True) else "Inactivo",
    }


def _cargar_filas():
    try:
        return [_doc_a_fila(d) for d in mongo_col("patrocinador").find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _dialogo_patrocinador(tabla, doc_id=None):
    col = mongo_col("patrocinador")
    doc = col.find_one({"_id": get_query_id(doc_id)}) if doc_id else {}

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:520px; max-height:80vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{RED};">'
                    f'{"✏  Editar Patrocinador" if doc_id else "＋  Nuevo Patrocinador"}</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(t): ui.html(f'<div class="section-label">{t}</div>')

        lbl("DATOS DEL PATROCINADOR")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_nombre  = ui.input("Nombre comercial",  value=doc.get("nombre", "")).props("outlined dark dense")
            inp_pais    = ui.input("País de origen",    value=doc.get("pais_origen", "")).props("outlined dark dense")
            inp_tipo    = ui.select(["principal", "tecnico", "otro"],
                                    value=doc.get("tipo", "principal"),
                                    label="Tipo de patrocinio").props("outlined dark dense")
            inp_activo  = ui.select(["activo","inactivo"],
                                    value="activo" if doc.get("activo", True) else "inactivo",
                                    label="Estado").props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            nuevo = {
                "nombre":            inp_nombre.value.strip(),
                "pais_origen":       inp_pais.value.strip(),
                "tipo":              inp_tipo.value,
                "activo":            inp_activo.value == "activo",
            }
            try:
                if doc_id:
                    col.update_one({"_id": get_query_id(doc_id)}, {"$set": nuevo})
                    ui.notify("Patrocinador actualizado ✓", type="positive")
                else:
                    col.insert_one(nuevo)
                    ui.notify("Patrocinador creado ✓", type="positive")
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
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};">¿Eliminar <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    mongo_col("patrocinador").delete_one({"_id": get_query_id(doc_id)})
                    ui.notify("Patrocinador eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/patrocinadores")
def page_patrocinadores():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/patrocinadores")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">PATROCINADORES</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">patrocinador</span></div>')
                ui.button("＋  Nuevo patrocinador", on_click=lambda: _dialogo_patrocinador(tabla)).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "nombre",     "label": "PATROCINADOR", "field": "nombre",     "sortable": True, "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "pais_origen","label": "PAÍS ORIGEN",  "field": "pais_origen", "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "tipo",       "label": "TIPO",         "field": "tipo",       "sortable": True, "align": "center"},
                {"name": "activo",     "label": "ESTADO",       "field": "activo",     "sortable": True, "align": "center"},
                {"name": "acciones",   "label": "ACCIONES",     "field": "acciones",   "sortable": False,"align": "center"},
            ]

            tabla = ui.table(columns=columnas, rows=_cargar_filas(), row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-tipo", """
                <q-td :props="props">
                  <span :class="{
                    'badge-gold':  props.value === 'principal',
                    'badge-green': props.value === 'tecnico',
                    'badge-blue':  props.value === 'oficial'
                  }" style="font-family:Courier New; font-size:0.78rem;">
                    {{ props.value.toUpperCase() }}
                  </span>
                </q-td>
            """)
            tabla.add_slot("body-cell-activo", """
                <q-td :props="props">
                  <span :class="props.value === 'Activo' ? 'badge-green' : 'badge-red'">
                    {{ props.value.toUpperCase() }}
                  </span>
                </q-td>
            """)
            tabla.add_slot("body-cell-acciones", """
                <q-td :props="props" style="text-align:center;">
                  <q-btn flat round dense icon="edit"   style="color:#F5C518; margin-right:4px;"
                    @click="$parent.$emit('editar', props.row)" />
                  <q-btn flat round dense icon="delete" style="color:#E8002A;"
                    @click="$parent.$emit('eliminar', props.row)" />
                </q-td>
            """)
            tabla.on("editar",   lambda e: _dialogo_patrocinador(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(tabla, e.args.get("_id"), e.args.get("nombre", "?")))
