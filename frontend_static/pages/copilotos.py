# frontend_static/pages/copilotos.py
# CRUD completo de copilotos · MongoDB

from nicegui import ui
from bson import ObjectId
from datetime import datetime, timezone
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc: dict) -> dict:
    pais = doc.get("pais", {})
    idiomas = doc.get("idiomas", [])
    fecha_nac = doc.get("fecha_nacimiento")
    fecha_str = fecha_nac.strftime("%Y-%m-%d") if isinstance(fecha_nac, datetime) else str(fecha_nac) if fecha_nac else "—"
    
    return {
        "_id":        str(doc.get("_id", "")),
        "nombre":     f'{doc.get("nombre","")} {doc.get("apellido","")}',
        "fecha_nac":  fecha_str,
        "pais":       pais.get("nombre", "—") if isinstance(pais, dict) else str(pais),
        "equipo":     doc.get("equipo_id", "—"),
        "piloto":     doc.get("piloto_id", "—"),
        "experiencia": doc.get("años_experiencia", 0),
        "idiomas":    ", ".join(idiomas) if isinstance(idiomas, list) else str(idiomas),
        "estado":     doc.get("estado", "activo"),
    }


def _cargar_filas():
    try:
        col = mongo_col("copiloto")
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


def _dialogo_copiloto(tabla, doc_id: str = None):
    col = mongo_col("copiloto")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

    pais = doc.get("pais", {})
    fecha_nac = doc.get("fecha_nacimiento")
    fecha_nac_str = fecha_nac.strftime("%Y-%m-%d") if isinstance(fecha_nac, datetime) else str(fecha_nac) if fecha_nac else ""

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:560px; max-height:80vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">'
                f'{"✏  Editar Copiloto" if doc_id else "＋  Nuevo Copiloto"}</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        lbl("DATOS PERSONALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_nombre   = ui.input("Nombre",   value=doc.get("nombre", "")).props("outlined dark dense")
            inp_apellido = ui.input("Apellido", value=doc.get("apellido", "")).props("outlined dark dense")
            inp_pais_cod = ui.input("Código País (ej: IT)", value=pais.get("codigo", "") if isinstance(pais, dict) else "").props("outlined dark dense")
            inp_pais_nom = ui.input("Nombre País", value=pais.get("nombre", "") if isinstance(pais, dict) else str(pais)).props("outlined dark dense")
            inp_fecha_nac = ui.input("Fecha Nacimiento (AAAA-MM-DD)", value=fecha_nac_str).props("outlined dark dense")
            inp_exp      = ui.number("Años de Experiencia", value=doc.get("años_experiencia", 0), format="%.0f").props("outlined dark dense")

        lbl("EQUIPO Y PILOTO RELACIONADO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_equipo   = ui.input("equipo_id",   value=doc.get("equipo_id", "")).props("outlined dark dense")
            inp_piloto   = ui.input("piloto_id",   value=doc.get("piloto_id", "")).props("outlined dark dense")
            inp_idiomas  = ui.input("Idiomas (separados por coma)", value=", ".join(doc.get("idiomas", [])) if isinstance(doc.get("idiomas"), list) else "").props("outlined dark dense").classes("col-span-2")
            inp_estado   = ui.select(
                ["activo", "inactivo"],
                value=doc.get("estado", "activo"),
                label="Estado"
            ).props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            f_nac = _parse_fecha(inp_fecha_nac.value)
            idiomas_list = [i.strip() for i in inp_idiomas.value.split(",") if i.strip()]
            
            nuevo = {
                "nombre":           inp_nombre.value.strip(),
                "apellido":         inp_apellido.value.strip(),
                "pais":             {"codigo": inp_pais_cod.value.strip().upper(), "nombre": inp_pais_nom.value.strip()},
                "equipo_id":        inp_equipo.value.strip(),
                "piloto_id":        inp_piloto.value.strip(),
                "años_experiencia": int(inp_exp.value or 0),
                "idiomas":          idiomas_list,
                "estado":           inp_estado.value,
            }
            if f_nac:
                nuevo["fecha_nacimiento"] = f_nac
            elif fecha_nac:
                nuevo["fecha_nacimiento"] = fecha_nac

            try:
                if doc_id:
                    col.update_one({"_id": get_query_id(doc_id)}, {"$set": nuevo})
                    ui.notify("Copiloto actualizado ✓", type="positive")
                else:
                    col.insert_one(nuevo)
                    ui.notify("Copiloto creado ✓", type="positive")
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
    col = mongo_col("copiloto")
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};font-size:1rem;">'
                f'¿Eliminar a copiloto <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    ui.notify("Copiloto eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/copilotos")
def page_copilotos():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/copilotos")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">COPILOTOS</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">copiloto</span></div>')
                ui.button("＋  Nuevo copiloto",
                          on_click=lambda: _dialogo_copiloto(tabla)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "nombre",      "label": "COPILOTO",    "field": "nombre",      "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "fecha_nac",   "label": "F. NACIMIENTO","field": "fecha_nac",   "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "pais",        "label": "PAÍS",        "field": "pais",        "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "equipo",      "label": "EQUIPO ID",   "field": "equipo",      "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "piloto",      "label": "PILOTO ID",   "field": "piloto",      "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "experiencia", "label": "EXP. (AÑOS)", "field": "experiencia", "sortable": True,  "align": "center", "style": f"color:{GOLD}; font-weight:bold;"},
                {"name": "idiomas",     "label": "IDIOMAS",     "field": "idiomas",     "sortable": False, "align": "left",   "style": f"color:{GREY};"},
                {"name": "estado",      "label": "ESTADO",      "field": "estado",      "sortable": True,  "align": "center"},
                {"name": "acciones",    "label": "ACCIONES",    "field": "acciones",    "sortable": False, "align": "center"},
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

            tabla.on("editar",   lambda e: _dialogo_copiloto(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("nombre", "?")))
