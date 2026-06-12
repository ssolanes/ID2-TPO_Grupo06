# frontend_static/pages/resumenes_carrera.py
# CRUD completo de resumenes de carrera · MongoDB

from nicegui import ui
from bson import ObjectId
from datetime import datetime, timezone
import json
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc: dict) -> dict:
    fecha_gen = doc.get("fecha_generacion")
    fecha_str = fecha_gen.strftime("%Y-%m-%d") if isinstance(fecha_gen, datetime) else str(fecha_gen) if fecha_gen else "—"
    
    podio = doc.get("podio", [])
    podio_parts = []
    for p in podio:
        podio_parts.append(f'P{p.get("puesto", "?")}: {p.get("pilot_id", "—")} ({p.get("tiempo_total", "")})')
    podio_str = " | ".join(podio_parts) if podio_parts else "—"

    incidentes = doc.get("incidentes", [])
    inc_str = f"{len(incidentes)} incidentes registrados"

    claves = doc.get("claves", [])
    claves_str = ", ".join(claves) if isinstance(claves, list) else str(claves)

    return {
        "_id":        str(doc.get("_id", "")),
        "rally_id":   doc.get("rally_id", "—"),
        "fecha_gen":  fecha_str,
        "podio":      podio_str,
        "incidentes": inc_str,
        "claves":     claves_str,
    }


def _cargar_filas():
    try:
        col = mongo_col("resumenes_carrera")
        return [_doc_a_fila(d) for d in col.find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _parse_fecha(fecha_str):
    if not fecha_str or not fecha_str.strip():
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(fecha_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _dialogo_resumen(tabla, doc_id: str = None):
    col = mongo_col("resumenes_carrera")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

    fecha_gen = doc.get("fecha_generacion")
    fecha_gen_str = fecha_gen.strftime("%Y-%m-%d") if isinstance(fecha_gen, datetime) else str(fecha_gen) if fecha_gen else ""

    podio_default = json.dumps([
        {"pilot_id": "piloto_moretti", "puesto": 1, "tiempo_total": "3:24:15.320"},
        {"pilot_id": "piloto_benitez", "puesto": 2, "tiempo_total": "3:24:48.711"},
        {"pilot_id": "piloto_tanaka", "puesto": 3, "tiempo_total": "3:25:10.004"}
    ], indent=2)

    incidentes_default = json.dumps([
        {
            "specialstage_id": "rally_fin_2026_ss4",
            "tipo": "falla_mecanica",
            "descripcion": "Descripción del incidente aquí..."
        }
    ], indent=2)

    podio_val = json.dumps(doc.get("podio", []), indent=2) if doc.get("podio") else podio_default
    incidentes_val = json.dumps(doc.get("incidentes", []), indent=2) if doc.get("incidentes") else incidentes_default
    abandons_val = json.dumps(doc.get("abandons", []), indent=2) if doc.get("abandons") else "[]"

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:680px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">'
                f'{"✏  Editar Resumen" if doc_id else "＋  Nuevo Resumen"}</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        lbl("DATOS GENERALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_rally = ui.input("rally_id", value=doc.get("rally_id", "")).props("outlined dark dense")
            inp_fecha = ui.input("Fecha Generación (AAAA-MM-DD)", value=fecha_gen_str).props("outlined dark dense")

        lbl("PODIO (JSON)")
        inp_podio = ui.textarea(value=podio_val).style(
            f"width:100%; font-family:Courier New; font-size:0.8rem; background:{CARD2}; color:{GREEN}; border:1px solid {BORDER}; border-radius:6px; padding:10px; min-height:100px;"
        ).props("outlined dark")

        lbl("ABANDONOS (JSON)")
        inp_abandons = ui.textarea(value=abandons_val).style(
            f"width:100%; font-family:Courier New; font-size:0.8rem; background:{CARD2}; color:{GREEN}; border:1px solid {BORDER}; border-radius:6px; padding:10px; min-height:60px;"
        ).props("outlined dark")

        lbl("INCIDENTES (JSON)")
        inp_incidentes = ui.textarea(value=incidentes_val).style(
            f"width:100%; font-family:Courier New; font-size:0.8rem; background:{CARD2}; color:{GREEN}; border:1px solid {BORDER}; border-radius:6px; padding:10px; min-height:100px;"
        ).props("outlined dark")

        lbl("PALABRAS CLAVE (separadas por coma)")
        inp_claves = ui.input(
            value=", ".join(doc.get("claves", [])) if isinstance(doc.get("claves"), list) else ""
        ).props("outlined dark dense").classes("w-full")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            f_gen = _parse_fecha(inp_fecha.value)
            
            try:
                podio_parsed = json.loads(inp_podio.value)
            except Exception:
                ui.notify("Error de formato JSON en Podio", type="negative")
                return

            try:
                abandons_parsed = json.loads(inp_abandons.value)
            except Exception:
                ui.notify("Error de formato JSON en Abandonos", type="negative")
                return

            try:
                incidentes_parsed = json.loads(inp_incidentes.value)
            except Exception:
                ui.notify("Error de formato JSON en Incidentes", type="negative")
                return

            claves_list = [c.strip() for c in inp_claves.value.split(",") if c.strip()]

            nuevo = {
                "rally_id":   inp_rally.value.strip(),
                "podio":      podio_parsed,
                "abandons":   abandons_parsed,
                "incidentes": incidentes_parsed,
                "claves":     claves_list,
            }
            
            if f_gen:
                nuevo["fecha_generacion"] = f_gen
            elif fecha_gen:
                nuevo["fecha_generacion"] = fecha_gen

            try:
                if doc_id:
                    col.update_one({"_id": get_query_id(doc_id)}, {"$set": nuevo})
                    ui.notify("Resumen de carrera actualizado ✓", type="positive")
                else:
                    col.insert_one(nuevo)
                    ui.notify("Resumen de carrera creado ✓", type="positive")
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
    col = mongo_col("resumenes_carrera")
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};font-size:1rem;">'
                f'¿Eliminar resumen de carrera para rally <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    ui.notify("Resumen eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/resumenes_carrera")
def page_resumenes_carrera():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/resumenes_carrera")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">RESÚMENES DE CARRERA</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">resumenes_carrera</span></div>')
                ui.button("＋  Nuevo resumen",
                          on_click=lambda: _dialogo_resumen(tabla)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "rally_id",   "label": "RALLY ID",     "field": "rally_id",    "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "fecha_gen",  "label": "F. GENERACIÓN","field": "fecha_gen",   "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "podio",      "label": "PODIO",        "field": "podio",       "sortable": False, "align": "left",   "style": f"color:{GOLD}; font-size:0.85rem;"},
                {"name": "incidentes", "label": "INCIDENTES",   "field": "incidentes",  "sortable": False, "align": "left",   "style": f"color:{GREY};"},
                {"name": "claves",     "label": "CLAVES",       "field": "claves",      "sortable": False, "align": "left",   "style": f"color:{GREY};"},
                {"name": "acciones",   "label": "ACCIONES",     "field": "acciones",    "sortable": False, "align": "center"},
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

            tabla.on("editar",   lambda e: _dialogo_resumen(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("rally_id", "?")))
