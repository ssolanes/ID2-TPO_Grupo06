# frontend_static/pages/equipos.py
# CRUD completo de equipos · MongoDB

from nicegui import ui
from bson import ObjectId
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc):
    return {
        "_id":          str(doc.get("_id", "")),
        "nombre":       doc.get("nombre", "—"),
        "pais":         doc.get("pais", "—"),
        "director":     doc.get("director_deportivo", "—"),
        "autos":        doc.get("vehiculo_oficial", "—"),
        "pilotos":      str(len(doc.get("pilotos_ids", []))),
        "victorias":    doc.get("estadisticas", {}).get("victorias", 0),
        "puntos":       doc.get("estadisticas", {}).get("puntos_constructores", 0),
        "temporadas":   doc.get("temporadas_activo", 0),
        "activo":       "Activo" if doc.get("activo", True) else "Inactivo",
    }


def _cargar_filas():
    try:
        return [_doc_a_fila(d) for d in mongo_col("equipos").find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _dialogo_equipo(tabla, doc_id=None):
    col = mongo_col("equipos")
    doc = col.find_one({"_id": ObjectId(doc_id)}) if doc_id else {}
    stats = doc.get("estadisticas", {})

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
            inp_pais      = ui.input("País",              value=doc.get("pais", "")).props("outlined dark dense")
            inp_director  = ui.input("Director deportivo",value=doc.get("director_deportivo", "")).props("outlined dark dense")
            inp_vehiculo  = ui.input("Vehículo oficial",  value=doc.get("vehiculo_oficial", "")).props("outlined dark dense")
            inp_temp      = ui.number("Temporadas activo",value=doc.get("temporadas_activo", 0), format="%.0f").props("outlined dark dense")
            inp_activo    = ui.select(["activo","inactivo"], value="activo" if doc.get("activo", True) else "inactivo",
                                      label="Estado").props("outlined dark dense")

        lbl("ESTADÍSTICAS")
        with ui.grid(columns=3).classes("w-full gap-2"):
            inp_pts  = ui.number("Puntos constructores", value=stats.get("puntos_constructores", 0), format="%.0f").props("outlined dark dense")
            inp_vics = ui.number("Victorias",            value=stats.get("victorias", 0),            format="%.0f").props("outlined dark dense")
            inp_pod  = ui.number("Podios",               value=stats.get("podios", 0),               format="%.0f").props("outlined dark dense")

        lbl("IDs RELACIONADOS (separados por coma)")
        inp_pilotos = ui.input(
            "pilotos_ids",
            value=", ".join(doc.get("pilotos_ids", []))
        ).props("outlined dark dense").classes("w-full")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            pilotos_list = [p.strip() for p in inp_pilotos.value.split(",") if p.strip()]
            nuevo = {
                "nombre":              inp_nombre.value.strip(),
                "pais":                inp_pais.value.strip(),
                "director_deportivo":  inp_director.value.strip(),
                "vehiculo_oficial":    inp_vehiculo.value.strip(),
                "temporadas_activo":   int(inp_temp.value or 0),
                "activo":              inp_activo.value == "activo",
                "pilotos_ids":         pilotos_list,
                "estadisticas": {
                    "puntos_constructores": int(inp_pts.value or 0),
                    "victorias":            int(inp_vics.value or 0),
                    "podios":               int(inp_pod.value or 0),
                },
            }
            try:
                if doc_id:
                    col.update_one({"_id": ObjectId(doc_id)}, {"$set": nuevo})
                    ui.notify("Equipo actualizado ✓", type="positive")
                else:
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
                    mongo_col("equipos").delete_one({"_id": ObjectId(doc_id)})
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
                {"name": "nombre",    "label": "EQUIPO",     "field": "nombre",    "sortable": True, "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "pais",      "label": "PAÍS",       "field": "pais",      "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "director",  "label": "DIRECTOR",   "field": "director",  "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "autos",     "label": "VEHÍCULO",   "field": "autos",     "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "pilotos",   "label": "PILOTOS",    "field": "pilotos",   "sortable": True, "align": "center", "style": f"color:{WHITE};"},
                {"name": "victorias", "label": "VIC",        "field": "victorias", "sortable": True, "align": "center", "style": f"color:{GOLD}; font-weight:bold;"},
                {"name": "puntos",    "label": "PTS CONST.", "field": "puntos",    "sortable": True, "align": "center", "style": f"color:{GOLD}; font-weight:bold;"},
                {"name": "temporadas","label": "TEMP.",      "field": "temporadas","sortable": True, "align": "center", "style": f"color:{GREY};"},
                {"name": "activo",    "label": "ESTADO",     "field": "activo",    "sortable": True, "align": "center"},
                {"name": "acciones",  "label": "ACCIONES",   "field": "acciones",  "sortable": False,"align": "center"},
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

            ui.html('<div class="section-label">SCHEMA · Documento ejemplo</div>')
            ui.html(
                '<div class="code-block">'
                '{ "_id": ObjectId,  "nombre": "Toyota Gazoo Racing WRT",\n'
                '  "pais": "Japón",  "director_deportivo": "Jari-Matti Latvala",\n'
                '  "vehiculo_oficial": "Toyota GR Yaris Rally1",\n'
                '  "pilotos_ids": ["wrc_ogier_01", "wrc_evans_17"],\n'
                '  "temporadas_activo": 8,  "activo": true,\n'
                '  "estadisticas": { "puntos_constructores": 550, "victorias": 17, "podios": 30 } }'
                '</div>'
            )
