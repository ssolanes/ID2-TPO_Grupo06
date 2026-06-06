# frontend_static/pages/rallies.py
# CRUD de rallies · MongoDB · estructura: legs → special_stages → splits

from nicegui import ui
from bson import ObjectId
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK
)


def _doc_a_fila(doc):
    legs = doc.get("legs", [])
    total_ss = sum(len(leg.get("special_stages", [])) for leg in legs)
    return {
        "_id":        str(doc.get("_id", "")),
        "nombre":     doc.get("nombre", "—"),
        "pais":       doc.get("pais", "—"),
        "temporada":  doc.get("temporada", "—"),
        "campeonato": doc.get("campeonato_id", "—"),
        "superficie": doc.get("superficie_principal", "—"),
        "legs":       len(legs),
        "ss":         total_ss,
        "estado":     doc.get("estado", "pendiente"),
    }


def _cargar_filas():
    try:
        return [_doc_a_fila(d) for d in mongo_col("rallies").find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _dialogo_rally(tabla, doc_id=None):
    col = mongo_col("rallies")
    doc = col.find_one({"_id": ObjectId(doc_id)}) if doc_id else {}
    legs_data = doc.get("legs", [])

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:700px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{RED};">'
                    f'{"✏  Editar Rally" if doc_id else "＋  Nuevo Rally"}</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(t): ui.html(f'<div class="section-label">{t}</div>')

        lbl("DATOS GENERALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_nombre  = ui.input("Nombre del rally",   value=doc.get("nombre", "")).props("outlined dark dense")
            inp_pais    = ui.input("País / Región",      value=doc.get("pais", "")).props("outlined dark dense")
            inp_sede    = ui.input("Sede / Ciudad base", value=doc.get("sede", "")).props("outlined dark dense")
            inp_camp    = ui.input("campeonato_id",      value=doc.get("campeonato_id", "wrc_2026")).props("outlined dark dense")
            inp_temp    = ui.number("Temporada",         value=doc.get("temporada", 2026), format="%.0f").props("outlined dark dense")
            inp_sup     = ui.select(["tierra","asfalto","nieve","mixto"],
                                    value=doc.get("superficie_principal","tierra"),
                                    label="Superficie").props("outlined dark dense")
            inp_estado  = ui.select(["pendiente","en_curso","finalizado"],
                                    value=doc.get("estado","pendiente"),
                                    label="Estado").props("outlined dark dense")

        # ── Legs / SS / Splits (simplificado: texto JSON) ──
        lbl("ESTRUCTURA DE LEGS · SPECIAL STAGES · SPLITS")
        ui.html(
            f'<div style="font-family:Courier New;font-size:0.78rem;color:{GREY};margin-bottom:6px;">'
            f'Editá los legs en formato JSON. Cada leg contiene special_stages con splits.</div>'
        )

        import json
        legs_default = json.dumps([{
            "numero_leg": 1,
            "fecha": "2026-08-14",
            "special_stages": [{
                "ss_id": "ss_ejemplo_01",
                "nombre": "Ascochinga 1",
                "distancia_km": 18.32,
                "superficie": "tierra",
                "splits": [
                    {"split_id": "ss_ejemplo_01_sp1", "numero": 1, "distancia_acumulada_km": 6.1, "tiempo_referencia_seg": 128.4},
                    {"split_id": "ss_ejemplo_01_sp2", "numero": 2, "distancia_acumulada_km": 12.7, "tiempo_referencia_seg": 267.9}
                ]
            }]
        }], indent=2)

        valor_legs = json.dumps(legs_data, default=str, indent=2) if legs_data else legs_default

        inp_legs = ui.textarea(value=valor_legs).style(
            f"width:100%; font-family:Courier New; font-size:0.8rem; "
            f"background:{CARD2}; color:{GREEN}; border:1px solid {BORDER}; "
            f"border-radius:6px; padding:10px; min-height:180px;"
        ).props("outlined dark")

        lbl("EQUIPOS PARTICIPANTES (IDs separados por coma)")
        inp_equipos = ui.input(
            value=", ".join(doc.get("equipos_participantes", []))
        ).props("outlined dark dense").classes("w-full")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            try:
                legs_parsed = json.loads(inp_legs.value)
            except Exception:
                ui.notify("Error en JSON de legs", type="negative")
                return
            equipos_list = [e.strip() for e in inp_equipos.value.split(",") if e.strip()]
            nuevo = {
                "nombre":               inp_nombre.value.strip(),
                "pais":                 inp_pais.value.strip(),
                "sede":                 inp_sede.value.strip(),
                "campeonato_id":        inp_camp.value.strip(),
                "temporada":            int(inp_temp.value or 2026),
                "superficie_principal": inp_sup.value,
                "estado":               inp_estado.value,
                "legs":                 legs_parsed,
                "equipos_participantes": equipos_list,
            }
            try:
                if doc_id:
                    col.update_one({"_id": ObjectId(doc_id)}, {"$set": nuevo})
                    ui.notify("Rally actualizado ✓", type="positive")
                else:
                    col.insert_one(nuevo)
                    ui.notify("Rally creado ✓", type="positive")
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
                    mongo_col("rallies").delete_one({"_id": ObjectId(doc_id)})
                    ui.notify("Rally eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/rallies")
def page_rallies():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/rallies")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">RALLIES · ETAPAS</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">rallies</span>'
                            f' → legs → special_stages → splits</div>')
                ui.button("＋  Nuevo rally", on_click=lambda: _dialogo_rally(tabla)).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "nombre",     "label": "RALLY",      "field": "nombre",     "sortable": True, "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "pais",       "label": "PAÍS",       "field": "pais",       "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "temporada",  "label": "TEMPORADA",  "field": "temporada",  "sortable": True, "align": "center", "style": f"color:{GREY};"},
                {"name": "campeonato", "label": "CAMPEONATO", "field": "campeonato", "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "superficie", "label": "SUPERFICIE", "field": "superficie", "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "legs",       "label": "LEGS",       "field": "legs",       "sortable": True, "align": "center", "style": f"color:{GOLD};"},
                {"name": "ss",         "label": "SS",         "field": "ss",         "sortable": True, "align": "center", "style": f"color:{GOLD};"},
                {"name": "estado",     "label": "ESTADO",     "field": "estado",     "sortable": True, "align": "center"},
                {"name": "acciones",   "label": "ACCIONES",   "field": "acciones",   "sortable": False,"align": "center"},
            ]

            tabla = ui.table(columns=columnas, rows=_cargar_filas(), row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-estado", """
                <q-td :props="props">
                  <span :class="{
                    'badge-green': props.value === 'finalizado',
                    'badge-gold':  props.value === 'en_curso',
                    'badge-red':   props.value === 'pendiente'
                  }">{{ props.value.toUpperCase() }}</span>
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
            tabla.on("editar",   lambda e: _dialogo_rally(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(tabla, e.args.get("_id"), e.args.get("nombre", "?")))

