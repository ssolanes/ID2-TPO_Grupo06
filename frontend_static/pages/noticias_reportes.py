# frontend_static/pages/noticias_reportes.py
# CRUD completo de noticias y reportes · MongoDB

from nicegui import ui
from datetime import datetime, timezone
from html import escape
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    sync_neo_node_from_doc, delete_neo_node_from_doc, mostrar_dialogo_relaciones,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL,
    TablaPaginada
)


def _doc_a_fila(doc: dict) -> dict:
    fecha_not = doc.get("fecha")
    fecha_str = fecha_not.strftime("%Y-%m-%d") if isinstance(fecha_not, datetime) else str(fecha_not) if fecha_not else "—"
    
    tags = doc.get("etiquetas", [])
    tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

    return {
        "_id":       str(doc.get("_id", "")),
        "titular":   doc.get("titular", "—"),
        "tipo":      doc.get("tipo", "—"),
        "fecha":     fecha_str,
        "contenido": doc.get("contenido", ""),
        "tags":      tags_str,
        "fuente":    doc.get("fuente", "—"),
    }


def _cargar_filas():
    try:
        col = mongo_col("noticias_reportes")
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


def _dialogo_noticia(tabla, doc_id: str = None):
    col = mongo_col("noticias_reportes")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

    fecha_not = doc.get("fecha")
    fecha_not_str = fecha_not.strftime("%Y-%m-%d") if isinstance(fecha_not, datetime) else str(fecha_not) if fecha_not else ""

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:600px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">'
                f'{"✏  Editar Reporte" if doc_id else "＋  Nuevo Reporte"}</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        lbl("DATOS GENERALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_titular = ui.input("Titular", value=doc.get("titular", "")).props("outlined dark dense").classes("col-span-2")
            inp_fecha   = ui.input("Fecha (AAAA-MM-DD)", value=fecha_not_str).props("outlined dark dense")
            inp_tipo    = ui.select(["incidente", "clima", "preview", "post_rally", "otro"], value=doc.get("tipo", "incidente"), label="Tipo de Reporte").props("outlined dark dense")
            inp_fuente  = ui.input("Fuente", value=doc.get("fuente", "FIA Official Media")).props("outlined dark dense")

        lbl("CONTENIDO DEL REPORTE")
        inp_contenido = ui.textarea(value=doc.get("contenido", "")).style(
            f"width:100%; font-family:Courier New; font-size:0.82rem; background:{CARD2}; color:{WHITE}; border:1px solid {BORDER}; border-radius:6px; padding:10px; min-height:120px;"
        ).props("outlined dark")

        lbl("ETIQUETAS / TAGS (separados por coma)")
        inp_tags = ui.input(
            value=", ".join(doc.get("etiquetas", [])) if isinstance(doc.get("etiquetas"), list) else ""
        ).props("outlined dark dense").classes("w-full")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            f_not = _parse_fecha(inp_fecha.value)
            tags_list = [t.strip() for t in inp_tags.value.split(",") if t.strip()]

            nuevo = {
                "titular":   inp_titular.value.strip(),
                "tipo":      inp_tipo.value,
                "contenido": inp_contenido.value.strip(),
                "etiquetas": tags_list,
                "fuente":    inp_fuente.value.strip(),
            }
            
            if f_not:
                nuevo["fecha"] = f_not
            elif fecha_not:
                nuevo["fecha"] = fecha_not

            try:
                if doc_id:
                    col.update_one(
                        {"_id": get_query_id(doc_id)},
                        {"$set": nuevo, "$unset": {"rally_id": ""}},
                    )
                    sync_neo_node_from_doc("NoticiaReporte", doc_id)
                    ui.notify("Reporte actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    result = col.insert_one(nuevo)
                    sync_neo_node_from_doc("NoticiaReporte", str(result.inserted_id))
                    ui.notify("Reporte creado en MongoDB y Neo4j ✓", type="positive")
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
    col = mongo_col("noticias_reportes")
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};font-size:1rem;">'
                f'¿Eliminar reporte <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    delete_neo_node_from_doc("NoticiaReporte", doc_id)
                    ui.notify("Reporte eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


def _dialogo_contenido(row: dict):
    titulo = escape(str(row.get("titular", "Reporte")))
    contenido = escape(str(row.get("contenido") or "—"))
    with ui.dialog() as dlg, \
         ui.card().style(
             f"background:{CARD}; border:1px solid {BORDER}; "
             f"width:min(760px, 92vw); max-height:82vh;"
         ):
        with ui.row().classes("w-full items-center justify-between").style("gap:12px;"):
            ui.html(
                f'<div style="font-family:Courier New;font-size:1rem;'
                f'font-weight:bold;color:{WHITE}; flex:1; min-width:0; '
                f'white-space:normal; overflow-wrap:anywhere; line-height:1.35;">'
                f'{titulo}</div>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        ui.html(
            f'<div style="font-family:Courier New;font-size:0.88rem;'
            f'line-height:1.55;color:{WHITE};white-space:pre-wrap;'
            f'background:{CARD2};border:1px solid {BORDER};border-radius:8px;'
            f'padding:14px;max-height:58vh;overflow-y:auto;">'
            f'{contenido}</div>'
        )

    dlg.open()


@ui.page("/static/noticias_reportes")
def page_noticias_reportes():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/noticias_reportes")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">NOTICIAS Y REPORTES</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">noticias_reportes</span></div>')
                ui.button("＋  Nuevo reporte",
                          on_click=lambda: _dialogo_noticia(tabla)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "titular",   "label": "TITULAR",      "field": "titular",     "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;"},
                {"name": "tipo",      "label": "TIPO",         "field": "tipo",        "sortable": True,  "align": "center"},
                {"name": "fecha",     "label": "FECHA",        "field": "fecha",       "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "contenido", "label": "CONTENIDO",    "field": "contenido",   "sortable": False, "align": "left",   "style": f"color:{GREY}; font-size:0.8rem; min-width:260px; max-width:420px;"},
                {"name": "tags",      "label": "ETIQUETAS",    "field": "tags",        "sortable": False, "align": "left",   "style": f"color:{GREEN}; font-size:0.8rem;"},
                {"name": "fuente",    "label": "FUENTE",       "field": "fuente",      "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "acciones",  "label": "ACCIONES",     "field": "acciones",    "sortable": False, "align": "center"},
            ]

            filas = _cargar_filas()

            tabla = TablaPaginada(columns=columnas, rows=filas, row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-tipo", """
                <q-td :props="props">
                  <span :class="{
                    'badge-red': props.value === 'incidente',
                    'badge-blue': props.value === 'clima',
                    'badge-gold': props.value === 'preview',
                    'badge-green': props.value === 'post_rally'
                  }">{{ props.value.toUpperCase() }}</span>
                </q-td>
            """)

            tabla.add_slot("body-cell-contenido", """
                <q-td :props="props" style="max-width:420px;">
                  <div style="display:flex; align-items:center; gap:8px; max-width:420px;">
                    <div style="font-family:Courier New; font-size:0.78rem; color:#8A8A9A; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; min-width:0;">
                      {{ props.value || '—' }}
                    </div>
                    <q-btn
                      flat
                      dense
                      size="sm"
                      icon="visibility"
                      style="color:#0080FF; flex:0 0 auto;"
                      @click="$parent.$emit('ver_contenido', props.row)"
                    />
                  </div>
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

            tabla.on("editar",   lambda e: _dialogo_noticia(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("titular", "?")))
            tabla.on("ver_contenido", lambda e: _dialogo_contenido(e.args))
