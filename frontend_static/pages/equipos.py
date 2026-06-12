# frontend_static/pages/equipos.py
# CRUD completo de equipos · MongoDB

from nicegui import ui
from bson import ObjectId
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc):
    vehiculos = doc.get("vehiculos_ids", [])
    patrocinadores = doc.get("patrocinadores_ids", [])
    return {
        "_id":             str(doc.get("_id", "")),
        "nombre":          doc.get("nombre", "—"),
        "pais_base":       doc.get("pais_base", "—"),
        "director":        doc.get("director", "—"),
        "jefe_ingenieria": doc.get("jefe_ingenieria_id", "—"),
        "autos":           ", ".join(vehiculos) if isinstance(vehiculos, list) else str(vehiculos),
        "pilotos":         str(len(doc.get("pilotos_ids", []))) if isinstance(doc.get("pilotos_ids"), list) else "0",
        "copilotos":       str(len(doc.get("copilotos_ids", []))) if isinstance(doc.get("copilotos_ids"), list) else "0",
        "patrocinadores":  ", ".join(patrocinadores) if isinstance(patrocinadores, list) else str(patrocinadores),
        "activo":          "Activo" if doc.get("activo", True) else "Inactivo",
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
            inp_jefe      = ui.input("Jefe de Ingeniería ID", value=doc.get("jefe_ingenieria_id", "")).props("outlined dark dense")
            inp_activo    = ui.select(["activo","inactivo"], value="activo" if doc.get("activo", True) else "inactivo",
                                      label="Estado").props("outlined dark dense")

        lbl("IDs RELACIONADOS (separados por coma)")
        with ui.grid(columns=1).classes("w-full gap-2"):
            inp_pilotos = ui.input(
                "Pilotos IDs",
                value=", ".join(doc.get("pilotos_ids", [])) if isinstance(doc.get("pilotos_ids"), list) else ""
            ).props("outlined dark dense").classes("w-full")
            
            inp_copilotos = ui.input(
                "Copilotos IDs",
                value=", ".join(doc.get("copilotos_ids", [])) if isinstance(doc.get("copilotos_ids"), list) else ""
            ).props("outlined dark dense").classes("w-full")

            inp_vehiculos = ui.input(
                "Vehículos IDs",
                value=", ".join(doc.get("vehiculos_ids", [])) if isinstance(doc.get("vehiculos_ids"), list) else ""
            ).props("outlined dark dense").classes("w-full")

            inp_patrocinadores = ui.input(
                "Patrocinadores IDs",
                value=", ".join(doc.get("patrocinadores_ids", [])) if isinstance(doc.get("patrocinadores_ids"), list) else ""
            ).props("outlined dark dense").classes("w-full")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            pilotos_list = [p.strip() for p in inp_pilotos.value.split(",") if p.strip()]
            copilotos_list = [c.strip() for c in inp_copilotos.value.split(",") if c.strip()]
            vehiculos_list = [v.strip() for v in inp_vehiculos.value.split(",") if v.strip()]
            patrocinadores_list = [s.strip() for s in inp_patrocinadores.value.split(",") if s.strip()]
            
            nuevo = {
                "nombre":              inp_nombre.value.strip(),
                "pais_base":           inp_pais.value.strip(),
                "director":            inp_director.value.strip(),
                "jefe_ingenieria_id":  inp_jefe.value.strip(),
                "activo":              inp_activo.value == "activo",
                "pilotos_ids":         pilotos_list,
                "copilotos_ids":       copilotos_list,
                "vehiculos_ids":       vehiculos_list,
                "patrocinadores_ids":  patrocinadores_list,
            }
            try:
                if doc_id:
                    col.update_one({"_id": get_query_id(doc_id)}, {"$set": nuevo})
                    ui.notify("Equipo actualizado ✓", type="positive")
                else:
                    # Si creamos uno nuevo sin _id especificado, mongo asigna ObjectId
                    col.insert_one(nuevo)
                    ui.notify("Equipo creado ✓", type="positive")
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
                {"name": "jefe_ingenieria", "label": "JEFE ING.",       "field": "jefe_ingenieria", "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "autos",           "label": "VEHÍCULOS",       "field": "autos",           "sortable": False,"align": "left",   "style": f"color:{GREY};"},
                {"name": "pilotos",         "label": "PILS",            "field": "pilotos",         "sortable": True, "align": "center", "style": f"color:{WHITE};"},
                {"name": "copilotos",       "label": "COPILS",          "field": "copilotos",       "sortable": True, "align": "center", "style": f"color:{WHITE};"},
                {"name": "patrocinadores",  "label": "SPONSORS",        "field": "patrocinadores",  "sortable": False,"align": "left",   "style": f"color:{GOLD};"},
                {"name": "activo",          "label": "ESTADO",          "field": "activo",          "sortable": True, "align": "center"},
                {"name": "acciones",        "label": "ACCIONES",        "field": "acciones",        "sortable": False,"align": "center"},
            ]

            tabla = ui.table(columns=columnas, rows=_cargar_filas(), row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

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
            tabla.on("editar",   lambda e: _dialogo_equipo(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(tabla, e.args.get("_id"), e.args.get("nombre", "?")))
