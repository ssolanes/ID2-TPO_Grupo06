# frontend_static/pages/pilotos.py
# CRUD completo de pilotos · MongoDB

from nicegui import ui
from bson import ObjectId
from datetime import datetime, timezone
import re
from uuid import uuid4
from frontend_static.shared import (
    mongo_col, neo4j_query, sidebar, GLOBAL_CSS, get_query_id,
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


def _nombre_completo(doc: dict) -> str:
    return f'{doc.get("nombre", "")} {doc.get("apellido", "")}'.strip()


def _slug(texto: str) -> str:
    limpio = re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")
    return limpio or uuid4().hex[:8]


def _id_disponible(coleccion: str, prefijo: str, base: str) -> str:
    candidato = f"{prefijo}_{_slug(base)}"
    if not mongo_col(coleccion).find_one({"_id": candidato}):
        return candidato
    return f"{candidato}_{uuid4().hex[:6]}"


def _buscar_doc(nombre_coleccion: str, doc_id: str):
    if not doc_id:
        return None
    return mongo_col(nombre_coleccion).find_one({"_id": get_query_id(doc_id)})


def _nombre_equipo(equipo_id: str) -> str:
    equipo = _buscar_doc("equipos", equipo_id)
    return equipo.get("nombre", equipo_id) if equipo else equipo_id


def _nombre_copiloto(copiloto_id: str) -> str:
    copiloto = _buscar_doc("copiloto", copiloto_id)
    return _nombre_completo(copiloto) if copiloto else copiloto_id


def _modelo_vehiculo(vehiculo_id: str) -> str:
    vehiculo = _buscar_doc("vehiculos", vehiculo_id)
    if not vehiculo:
        return vehiculo_id
    return f'{vehiculo.get("marca", "")} {vehiculo.get("modelo", "")}'.strip() or vehiculo_id


def _relacionar_nodo_neo4j(
    piloto_id: str,
    label: str,
    mongo_id: str,
    propiedad_nombre: str,
    valor_nombre: str,
    relacion: str,
):
    encontrados = neo4j_query(f"""
        MATCH (n:{label})
        WHERE n.mongo_id = $mongo_id OR n.{propiedad_nombre} = $valor_nombre
        RETURN elementId(n) AS element_id
        LIMIT 1
    """, {
        "mongo_id": mongo_id,
        "valor_nombre": valor_nombre,
    })

    if encontrados:
        neo4j_query(f"""
            MATCH (p:Piloto {{mongo_id: $piloto_id}})
            MATCH (n:{label})
            WHERE elementId(n) = $element_id
            SET n.mongo_id = coalesce(n.mongo_id, $mongo_id),
                n.{propiedad_nombre} = $valor_nombre
            MERGE (p)-[:{relacion}]->(n)
        """, {
            "piloto_id": piloto_id,
            "element_id": encontrados[0]["element_id"],
            "mongo_id": mongo_id,
            "valor_nombre": valor_nombre,
        })
        return

    neo4j_query(f"""
        MATCH (p:Piloto {{mongo_id: $piloto_id}})
        CREATE (n:{label} {{mongo_id: $mongo_id, {propiedad_nombre}: $valor_nombre}})
        MERGE (p)-[:{relacion}]->(n)
    """, {
        "piloto_id": piloto_id,
        "mongo_id": mongo_id,
        "valor_nombre": valor_nombre,
    })


def _sincronizar_piloto_neo4j(mongo_id: str, piloto: dict):
    nombre_completo = _nombre_completo(piloto)
    pais = piloto.get("pais", {})
    pais_nombre = pais.get("nombre", "") if isinstance(pais, dict) else str(pais or "")

    neo4j_query("""
        MERGE (p:Piloto {mongo_id: $mongo_id})
        SET p.nombre = $nombre_completo,
            p.nombre_pila = $nombre,
            p.apellido = $apellido,
            p.pais = $pais,
            p.numero_auto = $numero_auto,
            p.estado = $estado
        WITH p
        OPTIONAL MATCH (p)-[r:PERTENECE_A|CONDUCE|TIENE_COPILOTO]->()
        DELETE r
    """, {
        "mongo_id": mongo_id,
        "nombre_completo": nombre_completo,
        "nombre": piloto.get("nombre", ""),
        "apellido": piloto.get("apellido", ""),
        "pais": pais_nombre,
        "numero_auto": piloto.get("numero_auto", 0),
        "estado": piloto.get("estado", "activo"),
    })

    equipo_id = piloto.get("equipo_id", "")
    if equipo_id:
        _relacionar_nodo_neo4j(
            mongo_id, "Equipo", equipo_id, "nombre", _nombre_equipo(equipo_id), "PERTENECE_A"
        )

    vehiculo_id = piloto.get("vehiculo_id", "")
    if vehiculo_id:
        _relacionar_nodo_neo4j(
            mongo_id, "Vehiculo", vehiculo_id, "modelo", _modelo_vehiculo(vehiculo_id), "CONDUCE"
        )

    copiloto_id = piloto.get("copiloto_id", "")
    if copiloto_id:
        _relacionar_nodo_neo4j(
            mongo_id, "Copiloto", copiloto_id, "nombre", _nombre_copiloto(copiloto_id), "TIENE_COPILOTO"
        )


def _sincronizar_alta_completa_neo4j(datos: dict):
    _sincronizar_piloto_neo4j(datos["piloto_id"], datos["piloto"])

    neo4j_query("""
        MATCH (e:Equipo {mongo_id: $equipo_id})
        MATCH (v:Vehiculo {mongo_id: $vehiculo_id})
        MERGE (e)-[:USA]->(v)
    """, {
        "equipo_id": datos["equipo_id"],
        "vehiculo_id": datos["vehiculo_id"],
    })
    neo4j_query("""
        MERGE (s:Patrocinador {mongo_id: $sponsor_id})
        MATCH (e:Equipo {mongo_id: $equipo_id})
        SET s.nombre = $sponsor_nombre,
            s.industria = $sponsor_tipo
        MERGE (s)-[:PATROCINA]->(e)
    """, {
        "sponsor_id": datos["sponsor_id"],
        "sponsor_nombre": datos["sponsor"]["nombre"],
        "sponsor_tipo": datos["sponsor"]["tipo"],
        "equipo_id": datos["equipo_id"],
    })
    neo4j_query("""
        MATCH (c:Copiloto {mongo_id: $copiloto_id})
        MATCH (v:Vehiculo {mongo_id: $vehiculo_id})
        MERGE (c)-[:ASISTE_EN]->(v)
    """, {
        "copiloto_id": datos["copiloto_id"],
        "vehiculo_id": datos["vehiculo_id"],
    })


# ─── Dialogo CREAR / EDITAR ──────────────────────────────────────────────────

def _dialogo_piloto(tabla, doc_id: str = None):
    col = mongo_col("pilotos")
    doc = {}
    if doc_id:
        doc = col.find_one({"_id": get_query_id(doc_id)}) or {}

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
                    col.update_one({"_id": get_query_id(doc_id)}, {"$set": nuevo})
                    _sincronizar_piloto_neo4j(str(doc_id), nuevo)
                    ui.notify("Piloto actualizado en MongoDB y Neo4j ✓", type="positive")
                else:
                    resultado = col.insert_one(nuevo)
                    _sincronizar_piloto_neo4j(str(resultado.inserted_id), nuevo)
                    ui.notify("Piloto creado en MongoDB y Neo4j ✓", type="positive")
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


def _dialogo_alta_completa(tabla):
    sufijo = uuid4().hex[:5]
    nombre_base = f"Rally Nova {sufijo.upper()}"

    defaults = {
        "piloto_nombre": "Nuevo",
        "piloto_apellido": f"Piloto {sufijo.upper()}",
        "piloto_pais": "Argentina",
        "numero_auto": 40 + int(sufijo[:2], 16) % 50,
        "equipo_nombre": f"{nombre_base} Team",
        "equipo_pais": "Argentina",
        "director": "Director Deportivo",
        "copiloto_nombre": "Nuevo",
        "copiloto_apellido": f"Copiloto {sufijo.upper()}",
        "sponsor_nombre": f"{nombre_base} Energy",
        "sponsor_tipo": "principal",
        "vehiculo_marca": "Toyota",
        "vehiculo_modelo": f"GR Yaris Rally1 {sufijo.upper()}",
    }

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:720px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between").style("margin-bottom:8px;"):
            ui.html(
                f'<span style="font-family:Courier New;font-size:1.1rem;'
                f'font-weight:bold;color:{RED};">＋  Alta completa editable</span>'
            )
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(texto):
            ui.html(f'<div class="section-label">{texto}</div>')

        lbl("PILOTO")
        with ui.grid(columns=4).classes("w-full gap-2"):
            inp_piloto_nombre = ui.input("Nombre", value=defaults["piloto_nombre"]).props("outlined dark dense")
            inp_piloto_apellido = ui.input("Apellido", value=defaults["piloto_apellido"]).props("outlined dark dense")
            inp_piloto_pais = ui.input("País", value=defaults["piloto_pais"]).props("outlined dark dense")
            inp_numero = ui.number("N° auto", value=defaults["numero_auto"], format="%.0f").props("outlined dark dense")

        lbl("EQUIPO Y SPONSOR")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_equipo_nombre = ui.input("Equipo", value=defaults["equipo_nombre"]).props("outlined dark dense")
            inp_equipo_pais = ui.input("País base", value=defaults["equipo_pais"]).props("outlined dark dense")
            inp_director = ui.input("Director", value=defaults["director"]).props("outlined dark dense")
            inp_sponsor_nombre = ui.input("Sponsor", value=defaults["sponsor_nombre"]).props("outlined dark dense")
            inp_sponsor_tipo = ui.select(["principal", "tecnico", "oficial"], value=defaults["sponsor_tipo"], label="Tipo sponsor").props("outlined dark dense")

        lbl("COPILOTO Y VEHÍCULO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_copiloto_nombre = ui.input("Nombre copiloto", value=defaults["copiloto_nombre"]).props("outlined dark dense")
            inp_copiloto_apellido = ui.input("Apellido copiloto", value=defaults["copiloto_apellido"]).props("outlined dark dense")
            inp_vehiculo_marca = ui.input("Marca vehículo", value=defaults["vehiculo_marca"]).props("outlined dark dense")
            inp_vehiculo_modelo = ui.input("Modelo vehículo", value=defaults["vehiculo_modelo"]).props("outlined dark dense")

        lbl("IDS GENERADOS")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_piloto_id = ui.input("piloto_id", value=_id_disponible("pilotos", "piloto", f'{defaults["piloto_nombre"]}_{defaults["piloto_apellido"]}')).props("outlined dark dense")
            inp_equipo_id = ui.input("equipo_id", value=_id_disponible("equipos", "eq", defaults["equipo_nombre"])).props("outlined dark dense")
            inp_copiloto_id = ui.input("copiloto_id", value=_id_disponible("copiloto", "copiloto", f'{defaults["copiloto_nombre"]}_{defaults["copiloto_apellido"]}')).props("outlined dark dense")
            inp_vehiculo_id = ui.input("vehiculo_id", value=_id_disponible("vehiculos", "veh", defaults["vehiculo_modelo"])).props("outlined dark dense")
            inp_sponsor_id = ui.input("sponsor_id", value=_id_disponible("patrocinador", "sponsor", defaults["sponsor_nombre"])).props("outlined dark dense")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")

        def guardar():
            piloto_id = inp_piloto_id.value.strip()
            equipo_id = inp_equipo_id.value.strip()
            copiloto_id = inp_copiloto_id.value.strip()
            vehiculo_id = inp_vehiculo_id.value.strip()
            sponsor_id = inp_sponsor_id.value.strip()
            ids = [
                ("pilotos", piloto_id),
                ("equipos", equipo_id),
                ("copiloto", copiloto_id),
                ("vehiculos", vehiculo_id),
                ("patrocinador", sponsor_id),
            ]
            if any(not valor for _, valor in ids):
                ui.notify("Completá todos los IDs generados", type="warning")
                return
            existentes = [valor for coleccion, valor in ids if mongo_col(coleccion).find_one({"_id": valor})]
            if existentes:
                ui.notify(f"Ya existen estos IDs: {', '.join(existentes)}", type="warning")
                return

            sponsor = {
                "_id": sponsor_id,
                "nombre": inp_sponsor_nombre.value.strip(),
                "tipo": inp_sponsor_tipo.value,
                "pais_origen": inp_equipo_pais.value.strip(),
                "activo": True,
            }
            copiloto = {
                "_id": copiloto_id,
                "nombre": inp_copiloto_nombre.value.strip(),
                "apellido": inp_copiloto_apellido.value.strip(),
                "pais": {"codigo": "", "nombre": inp_piloto_pais.value.strip()},
                "equipo_id": equipo_id,
                "piloto_id": piloto_id,
                "años_experiencia": 0,
                "idiomas": ["español"],
                "estado": "activo",
            }
            vehiculo = {
                "_id": vehiculo_id,
                "marca": inp_vehiculo_marca.value.strip(),
                "modelo": inp_vehiculo_modelo.value.strip(),
                "anio": 2026,
                "equipo_id": equipo_id,
                "tipo_combustible": "hibrido",
                "motor": {
                    "hp": 500,
                    "velocidad_punta_kmh": 210,
                    "cilindrada_cc": 1600,
                    "torque_nm": 500,
                },
                "configuracion": {
                    "traccion": "4WD",
                    "transmision": "secuencial",
                    "suspension": "rally",
                },
                "estado_mecanico": {
                    "ok": True,
                    "falla_activa": None,
                    "ultima_revision": datetime.now(timezone.utc),
                },
            }
            equipo = {
                "_id": equipo_id,
                "nombre": inp_equipo_nombre.value.strip(),
                "pais_base": inp_equipo_pais.value.strip(),
                "director": inp_director.value.strip(),
                "jefe_ingenieria_id": "",
                "pilotos_ids": [piloto_id],
                "copilotos_ids": [copiloto_id],
                "vehiculos_ids": [vehiculo_id],
                "patrocinadores_ids": [sponsor_id],
                "activo": True,
            }
            piloto = {
                "_id": piloto_id,
                "nombre": inp_piloto_nombre.value.strip(),
                "apellido": inp_piloto_apellido.value.strip(),
                "pais": {"nombre": inp_piloto_pais.value.strip()},
                "numero_auto": int(inp_numero.value or 0),
                "equipo_id": equipo_id,
                "copiloto_id": copiloto_id,
                "vehiculo_id": vehiculo_id,
                "estado": "activo",
                "sponsors": [sponsor_id],
                "estadisticas": {
                    "puntos": 0,
                    "victorias": 0,
                    "podios": 0,
                    "rallies_disputados": 0,
                },
            }

            try:
                mongo_col("patrocinador").insert_one(sponsor)
                mongo_col("copiloto").insert_one(copiloto)
                mongo_col("vehiculos").insert_one(vehiculo)
                mongo_col("equipos").insert_one(equipo)
                mongo_col("pilotos").insert_one(piloto)
                _sincronizar_alta_completa_neo4j({
                    "piloto_id": piloto_id,
                    "equipo_id": equipo_id,
                    "copiloto_id": copiloto_id,
                    "vehiculo_id": vehiculo_id,
                    "sponsor_id": sponsor_id,
                    "piloto": piloto,
                    "sponsor": sponsor,
                })
                ui.notify("Alta completa creada en MongoDB y Neo4j ✓", type="positive")
                dlg.close()
                tabla.rows = _cargar_filas()
                tabla.update()
            except Exception as e:
                ui.notify(f"Error creando alta completa: {e}", type="negative")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            ui.button("Crear todo", on_click=guardar).props("unelevated").style(
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
                    col.delete_one({"_id": get_query_id(doc_id)})
                    neo4j_query("""
                        MATCH (p:Piloto {mongo_id: $mongo_id})
                        DETACH DELETE p
                    """, {"mongo_id": str(doc_id)})
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
                with ui.row().classes("gap-2"):
                    ui.button("＋  Alta completa",
                              on_click=lambda: _dialogo_alta_completa(tabla)
                    ).props("unelevated").style(
                        f"background:{BLUE}; color:white; font-family:Courier New; font-weight:bold;"
                    )
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
