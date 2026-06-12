# frontend_static/pages/vehiculos.py
# CRUD completo de vehículos · MongoDB

from nicegui import ui
from bson import ObjectId
from datetime import datetime, timezone
from frontend_static.shared import (
    mongo_col, sidebar, GLOBAL_CSS, get_query_id,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


def _doc_a_fila(doc: dict) -> dict:
    motor = doc.get("motor", {})
    motor_str = f'{motor.get("hp", "—")} HP / {motor.get("velocidad_punta_kmh", "—")} km/h'
    config = doc.get("configuracion", {})
    traccion = config.get("traccion", "—")
    
    mecanico = doc.get("estado_mecanico", {})
    revision_date = mecanico.get("ultima_revision")
    revision_str = revision_date.strftime("%Y-%m-%d") if isinstance(revision_date, datetime) else str(revision_date) if revision_date else "—"
    
    ok = mecanico.get("ok", True)
    falla = mecanico.get("falla_activa")
    
    if ok:
        estado_str = "OK"
    else:
        falla_tipo = falla.get("tipo", "Falla") if isinstance(falla, dict) else "Falla"
        falla_grav = falla.get("gravedad", "Alta") if isinstance(falla, dict) else "Alta"
        estado_str = f"{falla_tipo} ({falla_grav})"

    return {
        "_id":         str(doc.get("_id", "")),
        "modelo":      f'{doc.get("marca","")} {doc.get("modelo","")}',
        "equipo":      doc.get("equipo_id", "—"),
        "anio":        doc.get("anio", "—"),
        "combustible": doc.get("tipo_combustible", "—"),
        "motor":       motor_str,
        "traccion":    traccion,
        "revision":    revision_str,
        "ok":          ok,
        "estado_mec":  estado_str,
    }


def _cargar_filas():
    try:
        col = mongo_col("vehiculos")
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


def _dialogo_vehiculo(tabla, doc_id: str = None):
    col = mongo_col("vehiculos")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

    motor = doc.get("motor", {})
    config = doc.get("configuracion", {})
    mecanico = doc.get("estado_mecanico", {})
    falla = mecanico.get("falla_activa") or {}
    
    rev_date = mecanico.get("ultima_revision")
    rev_date_str = rev_date.strftime("%Y-%m-%d") if isinstance(rev_date, datetime) else str(rev_date) if rev_date else ""

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:640px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">'
                f'{"✏  Editar Vehículo" if doc_id else "＋  Nuevo Vehículo"}</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        lbl("DATOS GENERALES")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_marca    = ui.input("Marca",  value=doc.get("marca", "")).props("outlined dark dense")
            inp_modelo   = ui.input("Modelo", value=doc.get("modelo", "")).props("outlined dark dense")
            inp_anio     = ui.number("Año",   value=doc.get("anio", 2026), format="%.0f").props("outlined dark dense")
            inp_equipo   = ui.input("equipo_id", value=doc.get("equipo_id", "")).props("outlined dark dense")
            inp_combust  = ui.select(["hibrido", "nafta", "diesel", "electrico"], value=doc.get("tipo_combustible", "hibrido"), label="Combustible").props("outlined dark dense")

        lbl("MOTORIZACIÓN")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_hp       = ui.number("Potencia (HP)",     value=motor.get("hp", 0), format="%.1f").props("outlined dark dense")
            inp_vel      = ui.number("Velocidad Punta (kmh)", value=motor.get("velocidad_punta_kmh", 0), format="%.1f").props("outlined dark dense")
            inp_cc       = ui.number("Cilindrada (cc)",   value=motor.get("cilindrada_cc", 0), format="%.0f").props("outlined dark dense")
            inp_torque   = ui.number("Torque (Nm)",       value=motor.get("torque_nm", 0), format="%.0f").props("outlined dark dense")

        lbl("CONFIGURACIÓN DE CHASIS")
        with ui.grid(columns=3).classes("w-full gap-2"):
            inp_traccion = ui.input("Tracción (ej: 4WD)", value=config.get("traccion", "4WD")).props("outlined dark dense")
            inp_trans    = ui.input("Transmisión",        value=config.get("transmision", "")).props("outlined dark dense")
            inp_susp     = ui.input("Suspensión",         value=config.get("suspension", "")).props("outlined dark dense")

        lbl("ESTADO MECÁNICO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            chk_ok       = ui.checkbox("Estado mecánico OK (Sin Fallas)", value=mecanico.get("ok", True)).props("dark dense")
            inp_rev      = ui.input("Última Revisión (AAAA-MM-DD)", value=rev_date_str).props("outlined dark dense")
            inp_fallat   = ui.input("Tipo Falla Activa (ej: Motor)", value=falla.get("tipo", "") if isinstance(falla, dict) else "").props("outlined dark dense")
            inp_fallag   = ui.select(["Baja", "Media", "Alta"], value=falla.get("gravedad", "Media") if isinstance(falla, dict) else "Media", label="Gravedad Falla").props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            f_rev = _parse_fecha(inp_rev.value)
            
            falla_dict = None
            if not chk_ok.value:
                falla_dict = {
                    "tipo": inp_fallat.value.strip(),
                    "gravedad": inp_fallag.value
                }
            
            nuevo = {
                "marca":            inp_marca.value.strip(),
                "modelo":           inp_modelo.value.strip(),
                "anio":             int(inp_anio.value or 0),
                "equipo_id":        inp_equipo.value.strip(),
                "tipo_combustible": inp_combust.value,
                "motor": {
                    "hp":                 float(inp_hp.value or 0),
                    "velocidad_punta_kmh": float(inp_vel.value or 0),
                    "cilindrada_cc":      int(inp_cc.value or 0),
                    "torque_nm":          int(inp_torque.value or 0),
                },
                "configuracion": {
                    "traccion":    inp_traccion.value.strip(),
                    "transmision": inp_trans.value.strip(),
                    "suspension":  inp_susp.value.strip(),
                },
                "estado_mecanico": {
                    "ok":              chk_ok.value,
                    "falla_activa":    falla_dict,
                }
            }
            
            if f_rev:
                nuevo["estado_mecanico"]["ultima_revision"] = f_rev
            elif rev_date:
                nuevo["estado_mecanico"]["ultima_revision"] = rev_date

            try:
                if doc_id:
                    col.update_one({"_id": get_query_id(doc_id)}, {"$set": nuevo})
                    ui.notify("Vehículo actualizado ✓", type="positive")
                else:
                    col.insert_one(nuevo)
                    ui.notify("Vehículo creado ✓", type="positive")
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
    col = mongo_col("vehiculos")
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER};"):
        ui.html(f'<div style="font-family:Courier New;color:{WHITE};font-size:1rem;">'
                f'¿Eliminar vehículo <b style="color:{RED};">{nombre}</b>?</div>')
        with ui.row().classes("w-full justify-end gap-2").style("margin-top:12px;"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            def eliminar():
                try:
                    col.delete_one({"_id": get_query_id(doc_id)})
                    ui.notify("Vehículo eliminado", type="warning")
                    dlg.close()
                    tabla.rows = _cargar_filas()
                    tabla.update()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
            ui.button("Eliminar", on_click=eliminar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New;"
            )
    dlg.open()


@ui.page("/static/vehiculos")
def page_vehiculos():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/vehiculos")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">VEHÍCULOS</div>')
                    ui.html(f'<div class="wrc-label">Colección MongoDB: <span style="color:{GREEN};">vehiculos</span></div>')
                ui.button("＋  Nuevo vehículo",
                          on_click=lambda: _dialogo_vehiculo(tabla)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            columnas = [
                {"name": "modelo",     "label": "VEHÍCULO",    "field": "modelo",      "sortable": True,  "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
                {"name": "equipo",     "label": "EQUIPO ID",   "field": "equipo",      "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "anio",       "label": "AÑO",         "field": "anio",        "sortable": True,  "align": "center", "style": f"color:{GREY};"},
                {"name": "combustible","label": "COMBUSTIBLE", "field": "combustible", "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "motor",      "label": "MOTOR (HP/PUNTA)", "field": "motor",   "sortable": False, "align": "left",   "style": f"color:{GREY};"},
                {"name": "traccion",   "label": "TRACCIÓN",    "field": "traccion",    "sortable": True,  "align": "center", "style": f"color:{GREY};"},
                {"name": "revision",   "label": "ÚLT. REVISIÓN","field": "revision",   "sortable": True,  "align": "left",   "style": f"color:{GREY};"},
                {"name": "estado_mec", "label": "ESTADO MECÁNICO", "field": "estado_mec", "sortable": True, "align": "center"},
                {"name": "acciones",   "label": "ACCIONES",    "field": "acciones",    "sortable": False, "align": "center"},
            ]

            filas = _cargar_filas()

            tabla = ui.table(columns=columnas, rows=filas, row_key="_id").style(
                f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
            ).props("flat dark")

            tabla.add_slot("body-cell-estado_mec", """
                <q-td :props="props">
                  <span :class="props.row.ok ? 'badge-green' : 'badge-red'">
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

            tabla.on("editar",   lambda e: _dialogo_vehiculo(tabla, e.args.get("_id")))
            tabla.on("eliminar", lambda e: _confirmar_eliminar(
                tabla, e.args.get("_id"), e.args.get("modelo", "?")))
