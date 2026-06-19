# frontend_static/pages/rallies.py
# CRUD de rallies · MongoDB · estructura: legs → special_stages → splits

from nicegui import ui
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    sync_neo_node_from_doc, delete_neo_node_from_doc, mostrar_dialogo_relaciones,
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
        "superficie": doc.get("superficie_principal", "—"),
        "legs":       len(legs),
        "ss":         total_ss,
    }


def _cargar_filas():
    try:
        return [_doc_a_fila(d) for d in mongo_col("rallies").find()]
    except Exception as e:
        ui.notify(f"Error MongoDB: {e}", type="negative")
        return []


def _resumen_estructura(legs):
    if not legs:
        return 1, 3, 2
    legs_count = len(legs)
    ss_counts = [len(leg.get("special_stages", [])) for leg in legs]
    ss_por_leg = max(ss_counts) if ss_counts else 1
    split_counts = [
        len(ss.get("splits", []))
        for leg in legs
        for ss in leg.get("special_stages", [])
    ]
    splits_por_ss = max(split_counts) if split_counts else 2
    return legs_count, ss_por_leg, splits_por_ss


def _generar_legs(nombre_rally, superficie, legs_count, ss_por_leg, splits_por_ss):
    legs = []
    for leg_idx in range(1, int(legs_count) + 1):
        stages = []
        for ss_idx in range(1, int(ss_por_leg) + 1):
            global_ss = ((leg_idx - 1) * int(ss_por_leg)) + ss_idx
            splits = [
                {
                    "nombre": f"Split {split_idx}",
                    "km": 0,
                    "tiempo_objetivo": "",
                }
                for split_idx in range(1, int(splits_por_ss) + 1)
            ]
            stages.append({
                "nombre": f"SS{global_ss}",
                "kilometros": 0,
                "superficie": superficie,
                "splits": splits,
            })
        legs.append({
            "nombre": f"Leg {leg_idx}",
            "dia": f"Día {leg_idx}",
            "special_stages": stages,
        })
    return legs


def _dialogo_rally(tabla, doc_id=None):
    col = mongo_col("rallies")
    doc = col.find_one({"_id": get_query_id(doc_id)}) if doc_id else {}
    legs_data = doc.get("legs", [])
    legs_count, ss_por_leg, splits_por_ss = _resumen_estructura(legs_data)

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:560px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{RED};">'
                    f'{"✏  Editar Rally" if doc_id else "＋  Nuevo Rally"}</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(t): ui.html(f'<div class="section-label">{t}</div>')

        lbl("DATOS GENERALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_nombre  = ui.input("Nombre del rally",   value=doc.get("nombre", "")).props("outlined dark dense")
            inp_pais    = ui.input("País",               value=doc.get("pais", "")).props("outlined dark dense")
            inp_temp    = ui.number("Temporada",         value=doc.get("temporada", 2026), format="%.0f").props("outlined dark dense")
            inp_sup     = ui.select(["tierra","asfalto","nieve","mixto"],
                                    value=doc.get("superficie_principal","tierra"),
                                    label="Superficie").props("outlined dark dense")

        lbl("ESTRUCTURA SIMPLE")
        with ui.grid(columns=3).classes("w-full gap-2"):
            inp_legs_count = ui.number("Días / legs", value=legs_count, format="%.0f").props("outlined dark dense")
            inp_ss_por_leg = ui.number("Special stages por día", value=ss_por_leg, format="%.0f").props("outlined dark dense")
            inp_splits_por_ss = ui.number("Splits por special stage", value=splits_por_ss, format="%.0f").props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            if int(inp_legs_count.value or 0) < 1 or int(inp_ss_por_leg.value or 0) < 1 or int(inp_splits_por_ss.value or 0) < 1:
                ui.notify("La estructura debe tener al menos 1 día, 1 special stage y 1 split", type="warning")
                return

            legs_generados = _generar_legs(
                inp_nombre.value.strip(),
                inp_sup.value,
                int(inp_legs_count.value or 1),
                int(inp_ss_por_leg.value or 1),
                int(inp_splits_por_ss.value or 1),
            )
            
            nuevo = {
                "nombre":               inp_nombre.value.strip(),
                "pais":                 inp_pais.value.strip(),
                "temporada":            int(inp_temp.value or 2026),
                "superficie_principal": inp_sup.value,
                "legs":                 legs_generados,
            }

            try:
                if doc_id:
                    col.update_one(
                        {"_id": get_query_id(doc_id)},
                        {"$set": nuevo, "$unset": {
                            "sede": "",
                            "campeonato": "",
                            "fecha_inicio": "",
                            "fecha_fin": "",
                            "equipos_participantes_ids": "",
                        }},
                    )
                    sync_neo_node_from_doc("Rally", doc_id)
                    ui.notify("Rally actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    result = col.insert_one(nuevo)
                    sync_neo_node_from_doc("Rally", str(result.inserted_id))
                    ui.notify("Rally creado en MongoDB y Neo4j ✓", type="positive")
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
                    mongo_col("rallies").delete_one({"_id": get_query_id(doc_id)})
                    delete_neo_node_from_doc("Rally", doc_id)
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
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">rallies</span></div>')
                ui.button("＋  Nuevo rally", on_click=lambda: _dialogo_rally(tabla)).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "nombre",     "label": "RALLY",      "field": "nombre",     "sortable": True, "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "pais",       "label": "PAÍS",       "field": "pais",       "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "temporada",  "label": "TEMPORADA",  "field": "temporada",  "sortable": True, "align": "center", "style": f"color:{GREY};"},
                {"name": "superficie", "label": "SUPERFICIE", "field": "superficie", "sortable": True, "align": "left",   "style": f"color:{GREY};"},
                {"name": "legs",       "label": "LEGS",       "field": "legs",       "sortable": True, "align": "center", "style": f"color:{GOLD};"},
                {"name": "ss",         "label": "SS",         "field": "ss",         "sortable": True, "align": "center", "style": f"color:{GOLD};"},
                {"name": "acciones",   "label": "ACCIONES",   "field": "acciones",   "sortable": False,"align": "center"},
            ]

            tabla = ui.table(columns=columnas, rows=_cargar_filas(), row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-acciones", """
                <q-td :props="props" style="text-align:center;">
                  <q-btn flat round dense icon="link"   style="color:#0080FF; margin-right:4px;"
                    @click="$parent.$emit('relaciones', props.row)" />
                  <q-btn flat round dense icon="edit"   style="color:#F5C518; margin-right:4px;"
                    @click="$parent.$emit('editar', props.row)" />
                  <q-btn flat round dense icon="delete" style="color:#E8002A;"
                    @click="$parent.$emit('eliminar', props.row)" />
                </q-td>
            """)
            tabla.on("relaciones", lambda e: mostrar_dialogo_relaciones("Rally", e.args.get("_id"), e.args.get("nombre", "?")))
            tabla.on("editar",   lambda e: _dialogo_rally(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(tabla, e.args.get("_id"), e.args.get("nombre", "?")))
