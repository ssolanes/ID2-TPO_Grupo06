# frontend_realtime/pages/live_timing.py
# Live Timing · Redis (tiempos en vivo por split)
# Estructura Redis:
#   ZADD timing:{ss_id}  <tiempo_ms>  <piloto_id>         ← ranking por tramo
#   HSET piloto:{piloto_id}  nombre "Ogier" equipo "TGR"  ← info del piloto
#   SET  rally:activo  <rally_id>                          ← rally en curso

from nicegui import ui
from frontend_realtime.shared import (
    get_redis, sidebar, GLOBAL_CSS,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK, PANEL
)


# ─── helpers Redis ────────────────────────────────────────────────────────────

def _get_rally_activo() -> str:
    try:
        r = get_redis()
        return r.get("rally:activo") or "rally_arg_2026"
    except Exception:
        return "rally_arg_2026"


def _get_ss_ids(rally_id: str) -> list[str]:
    """Devuelve los ss_id que tienen datos en Redis para el rally dado."""
    try:
        r = get_redis()
        keys = r.keys(f"timing:{rally_id}:*")
        ss_ids = sorted(set(k.split(":")[-1] for k in keys))
        return ss_ids or ["ss_ejemplo_01"]
    except Exception:
        return ["ss_ejemplo_01"]


def _get_ranking(rally_id: str, ss_id: str) -> list[dict]:
    """Obtiene el ranking de un SS desde Redis ZASET."""
    try:
        r = get_redis()
        key = f"timing:{rally_id}:{ss_id}"
        items = r.zrange(key, 0, -1, withscores=True)
        filas = []
        for pos, (piloto_id, tiempo_ms) in enumerate(items, 1):
            info = r.hgetall(f"piloto:{piloto_id}") or {}
            seg = tiempo_ms / 1000
            filas.append({
                "pos":      pos,
                "piloto":   info.get("nombre", piloto_id),
                "equipo":   info.get("equipo", "—"),
                "numero":   info.get("numero", "—"),
                "tiempo":   f"{int(seg // 60)}:{seg % 60:06.3f}",
                "tiempo_ms": int(tiempo_ms),
            })
        # calcular gaps
        if filas:
            ref = filas[0]["tiempo_ms"]
            for f in filas:
                gap_ms = f["tiempo_ms"] - ref
                f["gap"] = "—" if gap_ms == 0 else f"+{gap_ms/1000:.3f}s"
        return filas
    except Exception as e:
        return []


def _get_splits(rally_id: str, ss_id: str, piloto_id: str) -> list[dict]:
    """Tiempos parciales de un piloto en splits individuales."""
    try:
        r = get_redis()
        splits_key = f"splits:{rally_id}:{ss_id}:{piloto_id}"
        raw = r.hgetall(splits_key)
        filas = []
        for sp_id, tiempo_ms in sorted(raw.items()):
            seg = float(tiempo_ms) / 1000
            filas.append({
                "split": sp_id,
                "tiempo": f"{int(seg // 60)}:{seg % 60:06.3f}",
            })
        return filas
    except Exception:
        return []


# ─── diálogos ─────────────────────────────────────────────────────────────────

def _dialogo_cargar_tiempo(rally_id: str, ss_id: str, contenedor_ranking):
    """Carga un tiempo manual para demo/testing."""
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:460px;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{RED};">'
                    f'⬤  Cargar tiempo · {ss_id}</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        ui.html(f'<div class="section-label">DATOS DEL TIEMPO</div>')
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_piloto  = ui.input("piloto_id (ej: wrc_ogier_01)").props("outlined dark dense")
            inp_nombre  = ui.input("Nombre piloto").props("outlined dark dense")
            inp_equipo  = ui.input("Equipo").props("outlined dark dense")
            inp_numero  = ui.input("N° auto").props("outlined dark dense")
        inp_tiempo = ui.number("Tiempo en milisegundos", value=120000, format="%.0f").props("outlined dark dense").classes("w-full")

        resultado = ui.html("")

        def guardar():
            try:
                r = get_redis()
                piloto_id = inp_piloto.value.strip()
                if not piloto_id:
                    ui.notify("Ingresá un piloto_id", type="warning")
                    return
                # guardar info piloto
                r.hset(f"piloto:{piloto_id}", mapping={
                    "nombre":  inp_nombre.value.strip() or piloto_id,
                    "equipo":  inp_equipo.value.strip() or "—",
                    "numero":  inp_numero.value.strip() or "—",
                })
                # cargar tiempo en ZSet
                key = f"timing:{rally_id}:{ss_id}"
                r.zadd(key, {piloto_id: float(inp_tiempo.value or 0)})
                ui.notify(f"Tiempo cargado ✓", type="positive")
                resultado.set_content(
                    f'<div style="font-family:Courier New;color:{GREEN};font-size:0.82rem;">'
                    f'ZADD {key}  {int(inp_tiempo.value)}  {piloto_id}</div>'
                )
                dlg.close()
                _refrescar_ranking(rally_id, ss_id, contenedor_ranking)
            except Exception as e:
                ui.notify(f"Error Redis: {e}", type="negative")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            ui.button("Cargar tiempo", on_click=guardar).props("unelevated").style(
                f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
            )
    dlg.open()


def _dialogo_set_rally(contenedor):
    """Cambia el rally activo en Redis."""
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:380px;"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{GOLD};">'
                    f'◎  Cambiar rally activo</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")
        ui.separator().style(f"background:{BORDER};")
        inp = ui.input("rally_id (ej: rally_arg_2026)", value=_get_rally_activo()).props("outlined dark dense").classes("w-full")

        def guardar():
            try:
                get_redis().set("rally:activo", inp.value.strip())
                ui.notify("Rally activo actualizado ✓", type="positive")
                dlg.close()
            except Exception as e:
                ui.notify(f"Error Redis: {e}", type="negative")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            ui.button("Guardar", on_click=guardar).props("unelevated").style(
                f"background:{GOLD}; color:{DARK}; font-family:Courier New; font-weight:bold;"
            )
    dlg.open()


# ─── render ranking ───────────────────────────────────────────────────────────

def _refrescar_ranking(rally_id: str, ss_id: str, contenedor):
    contenedor.clear()
    filas = _get_ranking(rally_id, ss_id)
    with contenedor:
        if not filas:
            ui.html(
                f'<div style="font-family:Courier New;color:{GREY};padding:16px;">'
                f'Sin datos para <b style="color:{GOLD};">{ss_id}</b> · '
                f'Cargá un tiempo con el botón ⬤  o verificá Redis.</div>'
            )
            return

        columnas = [
            {"name": "pos",    "label": "POS",    "field": "pos",    "sortable": True,  "align": "center", "style": f"color:{GOLD}; font-weight:bold; width:50px;"},
            {"name": "numero", "label": "#",      "field": "numero", "sortable": False, "align": "center", "style": f"color:{WHITE};"},
            {"name": "piloto", "label": "PILOTO", "field": "piloto", "sortable": False, "align": "left",   "style": f"color:{WHITE}; font-weight:bold;"},
            {"name": "equipo", "label": "EQUIPO", "field": "equipo", "sortable": False, "align": "left",   "style": f"color:{GREY};"},
            {"name": "tiempo", "label": "TIEMPO", "field": "tiempo", "sortable": False, "align": "center", "style": f"color:{GREEN}; font-weight:bold; font-family:Courier New;"},
            {"name": "gap",    "label": "GAP",    "field": "gap",    "sortable": False, "align": "center", "style": f"color:{GREY};"},
        ]
        tabla = ui.table(columns=columnas, rows=filas, row_key="piloto").style(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
        ).props("flat dark")
        tabla.add_slot("body-cell-pos", """
            <q-td :props="props">
              <span :style="props.value === 1 ? 'color:#F5C518;font-size:1.1rem;' :
                            props.value === 2 ? 'color:#C0C0C0;' :
                            props.value === 3 ? 'color:#CD7F32;' : ''">
                {{ props.value }}
              </span>
            </q-td>
        """)


# ─── página principal ─────────────────────────────────────────────────────────

@ui.page("/realtime/live_timing")
def page_live_timing():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    rally_id = _get_rally_activo()
    ss_ids   = _get_ss_ids(rally_id)
    ss_sel   = {"value": ss_ids[0] if ss_ids else "ss_ejemplo_01"}

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/realtime/live_timing")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):

            # Header
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(
                        f'<div class="wrc-title" style="font-size:1.6rem;">'
                        f'<span class="live-dot"></span>LIVE TIMING</div>'
                    )
                    ui.html(
                        f'<div class="wrc-label">Redis · '
                        f'<span style="color:{GOLD};">rally activo: {rally_id}</span></div>'
                    )
                with ui.row().classes("gap-2"):
                    ui.button("◎  Rally activo", on_click=lambda: _dialogo_set_rally(None)).props("flat").style(
                        f"color:{GOLD}; font-family:Courier New; border:1px solid {BORDER};"
                    )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            # Selector de SS
            ui.html(f'<div class="section-label">SPECIAL STAGE</div>')
            with ui.row().classes("items-center gap-3 w-full"):
                sel_ss = ui.select(
                    ss_ids,
                    value=ss_sel["value"],
                    label="Seleccioná un SS"
                ).props("outlined dark dense").style("min-width:220px;")

                contenedor_ranking = ui.column().classes("w-full")

                def cambiar_ss(e):
                    ss_sel["value"] = sel_ss.value
                    _refrescar_ranking(rally_id, sel_ss.value, contenedor_ranking)

                sel_ss.on("update:model-value", cambiar_ss)

                ui.button(
                    "⬤  Cargar tiempo",
                    on_click=lambda: _dialogo_cargar_tiempo(rally_id, sel_ss.value, contenedor_ranking)
                ).props("unelevated").style(
                    f"background:{RED}; color:white; font-family:Courier New; font-weight:bold;"
                )

                ui.button(
                    "↺  Refrescar",
                    on_click=lambda: _refrescar_ranking(rally_id, sel_ss.value, contenedor_ranking)
                ).props("flat").style(
                    f"color:{GREEN}; font-family:Courier New; border:1px solid {BORDER};"
                )

            # Ranking inicial
            _refrescar_ranking(rally_id, ss_sel["value"], contenedor_ranking)

            # Notas de estructura Redis
            ui.html('<div class="section-label" style="margin-top:20px;">ESTRUCTURA REDIS · KEYS</div>')
            ui.html(
                '<div class="code-block">'
                f'SET   rally:activo              → "{rally_id}"\n'
                f'ZADD  timing:{{rally_id}}:{{ss_id}}  <tiempo_ms>  <piloto_id>   ← ranking en vivo\n'
                f'HSET  piloto:{{piloto_id}}          nombre "Ogier" equipo "TGR" numero "1"\n'
                f'HSET  splits:{{rally_id}}:{{ss_id}}:{{piloto_id}}  sp1 <ms> sp2 <ms>  ← parciales\n\n'
                f'// Los ss_id son los mismos que en MongoDB (rallies.legs.special_stages.ss_id)\n'
                f'// Esto vincula los datos estáticos con los tiempos en vivo'
                '</div>'
            )
