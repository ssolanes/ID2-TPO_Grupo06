# frontend_static/pages/resumenes_carrera.py
# CRUD completo de resumenes de carrera · MongoDB

from nicegui import ui
from datetime import datetime, timezone
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    sync_neo_node_from_doc, delete_neo_node_from_doc, mostrar_dialogo_relaciones,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc: dict) -> dict:
    fecha_gen = doc.get("fecha_generacion")
    fecha_str = fecha_gen.strftime("%Y-%m-%d") if isinstance(fecha_gen, datetime) else str(fecha_gen) if fecha_gen else "—"
    
    incidentes = doc.get("incidentes", [])
    if isinstance(incidentes, list):
        inc_str = f"{len(incidentes)} incidentes registrados" if incidentes else "—"
    else:
        inc_str = str(incidentes)[:80] if incidentes else "—"

    claves = doc.get("claves", [])
    claves_str = ", ".join(claves) if isinstance(claves, list) else str(claves)

    podio = doc.get("podio", [])
    if isinstance(podio, list):
        podio_str = ", ".join(p.get("piloto", p.get("pilot_id", "")) for p in podio if isinstance(p, dict))
    else:
        podio_str = str(podio)

    return {
        "_id":        str(doc.get("_id", "")),
        "titulo":     doc.get("titulo", doc.get("rally_nombre", doc.get("rally_id", "Resumen"))),
        "fecha_gen":  fecha_str,
        "ganador":    doc.get("ganador", "—"),
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

    podio_actual = doc.get("podio", [])
    if isinstance(podio_actual, list):
        podio_val = ", ".join(p.get("piloto", p.get("pilot_id", "")) for p in podio_actual if isinstance(p, dict))
    else:
        podio_val = str(podio_actual)
    incidentes_actual = doc.get("incidentes", "")
    if isinstance(incidentes_actual, list):
        incidentes_val = "; ".join(i.get("descripcion", str(i)) for i in incidentes_actual if isinstance(i, dict))
    else:
        incidentes_val = str(incidentes_actual)

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
            inp_titulo = ui.input("Título", value=doc.get("titulo", doc.get("rally_nombre", ""))).props("outlined dark dense")
            inp_fecha = ui.input("Fecha Generación (AAAA-MM-DD)", value=fecha_gen_str).props("outlined dark dense")
            inp_ganador = ui.input("Ganador", value=doc.get("ganador", "")).props("outlined dark dense")

        lbl("PODIO")
        inp_podio = ui.input("Pilotos del podio (separados por coma)", value=podio_val).props("outlined dark dense").classes("w-full")

        lbl("INCIDENTES")
        inp_incidentes = ui.textarea(value=incidentes_val).style(
            f"width:100%; font-family:Courier New; font-size:0.82rem; background:{CARD2}; color:{WHITE}; border:1px solid {BORDER}; border-radius:6px; padding:10px; min-height:90px;"
        ).props("outlined dark")

        lbl("PALABRAS CLAVE (separadas por coma)")
        inp_claves = ui.input(
            value=", ".join(doc.get("claves", [])) if isinstance(doc.get("claves"), list) else ""
        ).props("outlined dark dense").classes("w-full")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            f_gen = _parse_fecha(inp_fecha.value)
            
            claves_list = [c.strip() for c in inp_claves.value.split(",") if c.strip()]
            podio_list = [
                {"puesto": idx, "piloto": piloto}
                for idx, piloto in enumerate([p.strip() for p in inp_podio.value.split(",") if p.strip()], start=1)
            ]

            nuevo = {
                "titulo":     inp_titulo.value.strip(),
                "ganador":    inp_ganador.value.strip(),
                "podio":      podio_list,
                "incidentes": inp_incidentes.value.strip(),
                "claves":     claves_list,
            }
            
            if f_gen:
                nuevo["fecha_generacion"] = f_gen
            elif fecha_gen:
                nuevo["fecha_generacion"] = fecha_gen

            try:
                if doc_id:
                    col.update_one(
                        {"_id": get_query_id(doc_id)},
                        {"$set": nuevo, "$unset": {"rally_id": "", "abandons": ""}},
                    )
                    sync_neo_node_from_doc("ResumenCarrera", doc_id)
                    ui.notify("Resumen de carrera actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    result = col.insert_one(nuevo)
                    sync_neo_node_from_doc("ResumenCarrera", str(result.inserted_id))
                    ui.notify("Resumen de carrera creado en MongoDB y Neo4j ✓", type="positive")
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
                f'¿Eliminar resumen <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    delete_neo_node_from_doc("ResumenCarrera", doc_id)
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
                {"name": "titulo",     "label": "TÍTULO",       "field": "titulo",      "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "fecha_gen",  "label": "F. GENERACIÓN","field": "fecha_gen",   "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "ganador",    "label": "GANADOR",      "field": "ganador",     "sortable": True,  "align": "left",   "style": f"color:{GOLD};"},
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

            tabla.on("relaciones", lambda e: mostrar_dialogo_relaciones("ResumenCarrera", e.args.get("_id"), e.args.get("titulo", "?")))
            tabla.on("editar",   lambda e: _dialogo_resumen(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("titulo", "?")))
