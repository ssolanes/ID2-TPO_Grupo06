# frontend_static/pages/pilotos.py
# CRUD completo de pilotos · MongoDB

from nicegui import ui
from bson import ObjectId
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _col(nombre):
    return mongo_col("pilotos")


# ─── Helpers ────────────────────────────────────────────────────────────────

def _doc_a_fila(doc: dict) -> dict:
    stats = doc.get("estadisticas", {})
    return {
        "_id":       str(doc.get("_id", "")),
        "numero":    doc.get("numero_auto", "—"),
        "nombre":    f'{doc.get("nombre","")} {doc.get("apellido","")}',
        "pais":      doc.get("pais", {}).get("nombre", "—") if isinstance(doc.get("pais"), dict) else doc.get("pais", "—"),
        "equipo":    doc.get("equipo_id", "—"),
        "copiloto":  doc.get("copiloto_id", "—"),
        "auto":      doc.get("vehiculo_id", "—"),
        "puntos":    stats.get("puntos", 0),
        "victorias": stats.get("victorias", 0),
        "estado":    doc.get("estado", "activo"),
    }


def _cargar_filas():
    try:
        col = mongo_col("pilotos")
        return [_doc_a_fila(d) for d in col.find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


# ─── Dialogo CREAR / EDITAR ──────────────────────────────────────────────────

def _dialogo_piloto(tabla, doc_id: str = None):
    col = mongo_col("pilotos")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": ObjectId(doc_id)}) or {}

    stats = doc.get("estadisticas", {})
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
            inp_num      = ui.input("N° auto",  value=str(doc.get("numero_auto", ""))).props("outlined dark dense")

        lbl("EQUIPO Y VEHÍCULO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_equipo   = ui.input("equipo_id",   value=doc.get("equipo_id", "")).props("outlined dark dense")
            inp_copiloto = ui.input("copiloto_id", value=doc.get("copiloto_id", "")).props("outlined dark dense")
            inp_vehiculo = ui.input("vehiculo_id", value=doc.get("vehiculo_id", "")).props("outlined dark dense")
            inp_estado   = ui.select(
                ["activo", "inactivo", "retirado"],
                value=doc.get("estado", "activo"),
                label="Estado"
            ).props("outlined dark dense")

        lbl("ESTADÍSTICAS")
        with ui.grid(columns=3).classes("w-full gap-2"):
            inp_pts  = ui.number("Puntos",    value=stats.get("puntos", 0),    format="%.0f").props("outlined dark dense")
            inp_vics = ui.number("Victorias", value=stats.get("victorias", 0), format="%.0f").props("outlined dark dense")
            inp_pod  = ui.number("Podios",    value=stats.get("podios", 0),    format="%.0f").props("outlined dark dense")
            inp_rd   = ui.number("Rallies disputados", value=stats.get("rallies_disputados", 0), format="%.0f").props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            nuevo = {
                "nombre":      inp_nombre.value.strip(),
                "apellido":    inp_apellido.value.strip(),
                "pais":        {"nombre": inp_pais.value.strip()},
                "numero_auto": int(inp_num.value or 0),
                "equipo_id":   inp_equipo.value.strip(),
                "copiloto_id": inp_copiloto.value.strip(),
                "vehiculo_id": inp_vehiculo.value.strip(),
                "estado":      inp_estado.value,
                "estadisticas": {
                    "puntos":              int(inp_pts.value or 0),
                    "victorias":           int(inp_vics.value or 0),
                    "podios":              int(inp_pod.value or 0),
                    "rallies_disputados":  int(inp_rd.value or 0),
                },
            }
            try:
                if doc_id:
                    col.update_one({"_id": ObjectId(doc_id)}, {"$set": nuevo})
                    ui.notify("Piloto actualizado ✓", type="positive")
                else:
                    col.insert_one(nuevo)
                    ui.notify("Piloto creado ✓", type="positive")
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
                    col.delete_one({"_id": ObjectId(doc_id)})
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
                {"name": "numero",    "label": "#",         "field": "numero",    "sortable": True,  "align": "center", "style": f"color:{GOLD}; font-weight:bold; width:50px;"},
                {"name": "nombre",    "label": "PILOTO",    "field": "nombre",    "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "pais",      "label": "PAÍS",      "field": "pais",      "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "equipo",    "label": "EQUIPO ID", "field": "equipo",    "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "copiloto",  "label": "COPILOTO",  "field": "copiloto",  "sortable": False, "align": "left",   "style": f"color:{GREY};"},
                {"name": "auto",      "label": "VEHÍCULO",  "field": "auto",      "sortable": False, "align": "left",   "style": f"color:{GREY};"},
                {"name": "puntos",    "label": "PTS",       "field": "puntos",    "sortable": True,  "align": "center", "style": f"color:{GOLD}; font-weight:bold;"},
                {"name": "victorias", "label": "VIC",       "field": "victorias", "sortable": True,  "align": "center", "style": f"color:{WHITE};"},
                {"name": "estado",    "label": "ESTADO",    "field": "estado",    "sortable": True,  "align": "center"},
                {"name": "acciones",  "label": "ACCIONES",  "field": "acciones",  "sortable": False, "align": "center"},
            ]

            filas = _cargar_filas()

            tabla = ui.table(columns=columnas, rows=filas, row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-estado", """
                <q-td :props="props">
                  <span :class="props.value === 'activo' ? 'badge-green' : 'badge-red'">
                    {{ props.value.toUpperCase() }}
                  </span>
                </q-td>
            """)

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

