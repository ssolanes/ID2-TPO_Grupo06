# frontend_static/pages/neo4j_relaciones.py
# Visualización de relaciones · Neo4j

from nicegui import ui
from frontend_static.shared import (
    mongo_col, neo4j_query, sidebar, GLOBAL_CSS,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK
)

# CRUD (hay que modificarlo)

RELACIONES_POR_ORIGEN = {
    "Piloto": [
        ("PERTENECE_A", "Equipo"),
        ("CONDUCE", "Vehiculo"),
        ("TIENE_COPILOTO", "Copiloto"),
        ("PARTICIPA_EN", "Campeonato"),
    ],
    "Copiloto": [
        ("PERTENECE_A", "Equipo"),
        ("ASISTE_EN", "Vehiculo"),
        ("PARTICIPA_EN", "Campeonato"),
    ],
    "Equipo": [
        ("USA", "Vehiculo"),
        ("PARTICIPA_EN", "Rally"),
    ],
    "Patrocinador": [
        ("PATROCINA", "Equipo"),
    ],
    "JefeIngenieria": [
        ("DIRIGE", "Equipo"),
    ],
    "Temporada": [
        ("TIENE_CAMPEONATO", "Campeonato"),
    ],
    "Campeonato": [
        ("TIENE_RALLY", "Rally"),
    ],
    "NoticiaReporte": [
        ("HABLA_DE", "Rally"),
    ],
    "ResumenCarrera": [
        ("RESUME", "Rally"),
    ],
}


TIPOS_AMIGABLES = {
    "Piloto": "Piloto",
    "Copiloto": "Copiloto",
    "Equipo": "Equipo",
    "Vehiculo": "Vehículo",
    "Patrocinador": "Patrocinador",
    "JefeIngenieria": "Jefe de ingeniería",
    "Temporada": "Temporada",
    "Campeonato": "Campeonato",
    "Rally": "Rally",
    "NoticiaReporte": "Noticia / reporte",
    "ResumenCarrera": "Resumen de carrera",
}


RELACIONES_AMIGABLES = {
    ("Piloto", "PERTENECE_A", "Equipo"): "Pertenece a un equipo",
    ("Piloto", "CONDUCE", "Vehiculo"): "Conduce un vehículo",
    ("Piloto", "TIENE_COPILOTO", "Copiloto"): "Tiene copiloto",
    ("Piloto", "PARTICIPA_EN", "Campeonato"): "Participa en campeonato",
    ("Copiloto", "PERTENECE_A", "Equipo"): "Pertenece a un equipo",
    ("Copiloto", "ASISTE_EN", "Vehiculo"): "Asiste en un vehículo",
    ("Copiloto", "PARTICIPA_EN", "Campeonato"): "Participa en campeonato",
    ("Equipo", "USA", "Vehiculo"): "Usa un vehículo",
    ("Equipo", "PARTICIPA_EN", "Rally"): "Participa en rally",
    ("Patrocinador", "PATROCINA", "Equipo"): "Patrocina un equipo",
    ("JefeIngenieria", "DIRIGE", "Equipo"): "Dirige un equipo",
    ("Temporada", "TIENE_CAMPEONATO", "Campeonato"): "Tiene campeonato",
    ("Campeonato", "TIENE_RALLY", "Rally"): "Tiene rally",
    ("NoticiaReporte", "HABLA_DE", "Rally"): "Habla de un rally",
    ("ResumenCarrera", "RESUME", "Rally"): "Resume un rally",
}


def _tipo_amigable(label: str) -> str:
    return TIPOS_AMIGABLES.get(label, label)


def _relacion_amigable(origen: str, rel: str, destino: str) -> str:
    return RELACIONES_AMIGABLES.get((origen, rel, destino), rel.replace("_", " ").title())


def _labels_existentes():
    try:
        rows = _cargar_labels()
        existentes = {row["label"] for row in rows}
        return [label for label in RELACIONES_POR_ORIGEN if label in existentes]
    except Exception:
        return list(RELACIONES_POR_ORIGEN)


def _opciones_nodos(label: str):
    rows = neo4j_query(f"""
        MATCH (n:{label})
        RETURN elementId(n) AS id,
               coalesce(n.nombre, n.modelo, n.titular, n.titulo, n.mongo_id, '-') AS nombre,
               coalesce(n.mongo_id, '') AS mongo_id
        ORDER BY nombre
        LIMIT 200
    """)
    opciones = {}
    for row in rows:
        opciones[row["id"]] = row.get("nombre", "-")
    return opciones


def _opciones_relaciones(label_origen: str):
    return {
        f"{rel}|{destino}": _relacion_amigable(label_origen, rel, destino)
        for rel, destino in RELACIONES_POR_ORIGEN.get(label_origen, [])
    }


def _parse_relacion(valor: str):
    rel, destino = valor.split("|", 1)
    return rel, destino


ENTIDADES_MONGO = {
    "Piloto": {
        "coleccion": "pilotos",
        "prop_nombre": "nombre",
        "label": "Piloto",
    },
    "Copiloto": {
        "coleccion": "copiloto",
        "prop_nombre": "nombre",
        "label": "Copiloto",
    },
    "Equipo": {
        "coleccion": "equipos",
        "prop_nombre": "nombre",
        "label": "Equipo",
    },
    "Vehiculo": {
        "coleccion": "vehiculos",
        "prop_nombre": "modelo",
        "label": "Vehiculo",
    },
    "Patrocinador": {
        "coleccion": "patrocinador",
        "prop_nombre": "nombre",
        "label": "Patrocinador",
    },
    "JefeIngenieria": {
        "coleccion": "jefe_ingenieria",
        "prop_nombre": "nombre",
        "label": "JefeIngenieria",
    },
    "Rally": {
        "coleccion": "rallies",
        "prop_nombre": "nombre",
        "label": "Rally",
    },
    "NoticiaReporte": {
        "coleccion": "noticias_reportes",
        "prop_nombre": "titular",
        "label": "NoticiaReporte",
    },
    "ResumenCarrera": {
        "coleccion": "resumenes_carrera",
        "prop_nombre": "titulo",
        "label": "ResumenCarrera",
    },
}


def _nombre_completo(doc):
    return f'{doc.get("nombre", "")} {doc.get("apellido", "")}'.strip()


def _display_doc(tipo, doc):
    if tipo in ("Piloto", "Copiloto", "JefeIngenieria"):
        nombre = _nombre_completo(doc)
    elif tipo == "Vehiculo":
        nombre = f'{doc.get("marca", "")} {doc.get("modelo", "")}'.strip()
    elif tipo == "NoticiaReporte":
        nombre = doc.get("titular", str(doc.get("_id", "")))
    elif tipo == "ResumenCarrera":
        nombre = doc.get("titulo", str(doc.get("_id", "")))
    else:
        nombre = doc.get("nombre", str(doc.get("_id", "")))
    return nombre or str(doc.get("_id", ""))


def _nodo_neo_para_doc(tipo, doc):
    meta = ENTIDADES_MONGO[tipo]
    label = meta["label"]
    prop_nombre = meta["prop_nombre"]
    mongo_id = str(doc.get("_id", ""))
    display = _display_doc(tipo, doc)
    rows = neo4j_query(f"""
        MATCH (n:{label})
        WHERE n.mongo_id = $mongo_id OR n.{prop_nombre} = $display
        RETURN elementId(n) AS id
        LIMIT 1
    """, {"mongo_id": mongo_id, "display": display})
    return rows[0]["id"] if rows else None


def _existe_relacion(element_id, patron):
    rows = neo4j_query(f"""
        MATCH (n)
        WHERE elementId(n) = $element_id
        RETURN EXISTS {{ MATCH {patron} }} AS existe
    """, {"element_id": element_id})
    return bool(rows and rows[0]["existe"])


def _dialogo_crear_relacion():
    labels_origen = _labels_existentes()
    if not labels_origen:
        ui.notify("No hay nodos disponibles para crear relaciones", type="warning")
        return
    label_inicial = "Piloto" if "Piloto" in labels_origen else labels_origen[0]
    relaciones_iniciales = _opciones_relaciones(label_inicial)
    if not relaciones_iniciales:
        ui.notify("Ese tipo de nodo no tiene relaciones configuradas", type="warning")
        return
    rel_inicial = next(iter(relaciones_iniciales))
    _, destino_inicial = _parse_relacion(rel_inicial)
    opciones_origen = _opciones_nodos(label_inicial)
    opciones_destino = _opciones_nodos(destino_inicial)

    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:620px; max-height:85vh; overflow-y:auto;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{BLUE};">⬡  Crear Relación Neo4j</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(t): ui.html(f'<div class="section-label">{t}</div>')

        lbl("NODO ORIGEN")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_label_a = ui.select(
                {label: _tipo_amigable(label) for label in labels_origen},
                value=label_inicial,
                label="Tipo de nodo",
            ).props("outlined dark dense")
            inp_nodo_a = ui.select(
                opciones_origen,
                value=next(iter(opciones_origen), None),
                label="Nodo origen",
            ).props("outlined dark dense")

        lbl("RELACIÓN POSIBLE")
        inp_rel = ui.select(
            relaciones_iniciales,
            value=rel_inicial,
            label="Relación según el tipo de origen",
        ).props("outlined dark dense").classes("w-full")

        lbl("NODO DESTINO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_label_b = ui.input("Tipo destino", value=_tipo_amigable(destino_inicial)).props("outlined dark dense readonly")
            inp_nodo_b = ui.select(
                opciones_destino,
                value=next(iter(opciones_destino), None),
                label="Nodo destino",
            ).props("outlined dark dense")

        resultado = ui.html("")

        def actualizar_destino():
            if not inp_rel.value:
                inp_label_b.value = ""
                inp_nodo_b.set_options({}, value=None)
                return
            _, destino = _parse_relacion(inp_rel.value)
            inp_label_b.value = _tipo_amigable(destino)
            destino_opciones = _opciones_nodos(destino)
            inp_nodo_b.set_options(destino_opciones, value=next(iter(destino_opciones), None))
            inp_label_b.update()

        def actualizar_origen():
            label = inp_label_a.value
            origen_opciones = _opciones_nodos(label)
            inp_nodo_a.set_options(origen_opciones, value=next(iter(origen_opciones), None))
            relaciones = _opciones_relaciones(label)
            inp_rel.set_options(relaciones, value=next(iter(relaciones), None))
            actualizar_destino()

        inp_label_a.on_value_change(lambda _: actualizar_origen())
        inp_rel.on_value_change(lambda _: actualizar_destino())

        def crear():
            if not inp_nodo_a.value or not inp_rel.value or not inp_nodo_b.value:
                ui.notify("Elegí nodo origen, relación y nodo destino", type="warning")
                return

            rel_tipo, destino_label = _parse_relacion(inp_rel.value)
            rel_nombre = _relacion_amigable(inp_label_a.value, rel_tipo, destino_label)

            try:
                neo4j_query(f"""
                    MATCH (a:{inp_label_a.value})
                    WHERE elementId(a) = $origen_id
                    MATCH (b:{destino_label})
                    WHERE elementId(b) = $destino_id
                    MERGE (a)-[r:{rel_tipo}]->(b)
                    RETURN r
                """, {
                    "origen_id": inp_nodo_a.value,
                    "destino_id": inp_nodo_b.value,
                })
                ui.notify(f"{rel_nombre} creada ✓", type="positive")
                resultado.set_content(
                    f'<div style="font-family:Courier New;color:{GREEN};font-size:0.82rem;">'
                    f'✓ {_tipo_amigable(inp_label_a.value)} · {rel_nombre} · {_tipo_amigable(destino_label)}</div>'
                )
            except Exception as e:
                ui.notify(f"Error Neo4j: {e}", type="negative")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            ui.button("Crear relación", on_click=crear).props("unelevated").style(
                f"background:{BLUE}; color:white; font-family:Courier New; font-weight:bold;"
            )
    dlg.open()


def _cargar_labels():
    return neo4j_query("""
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, count(*) AS cantidad
        ORDER BY label
    """)


def _cargar_relaciones():
    rows = neo4j_query("""
        MATCH (a)-[r]->(b)
        RETURN labels(a)[0] AS origen_tipo,
               coalesce(a.nombre, a.modelo, a.mongo_id, '-') AS origen,
               type(r) AS relacion_codigo,
               labels(b)[0] AS destino_tipo,
               coalesce(b.nombre, b.modelo, b.titular, b.titulo, b.mongo_id, '-') AS destino
        ORDER BY origen_tipo, relacion_codigo, destino_tipo
        LIMIT 250
    """)
    for row in rows:
        row["relacion"] = _relacion_amigable(
            row.get("origen_tipo", ""),
            row.get("relacion_codigo", ""),
            row.get("destino_tipo", ""),
        )
        row["origen_tipo"] = _tipo_amigable(row.get("origen_tipo", ""))
        row["destino_tipo"] = _tipo_amigable(row.get("destino_tipo", ""))
    return rows


def _cargar_nodos_sueltos():
    rows = neo4j_query("""
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n)[0] AS tipo,
               coalesce(n.nombre, n.modelo, n.titular, n.titulo, n.mongo_id, '-') AS nombre,
               coalesce(n.mongo_id, '') AS mongo_id
        ORDER BY tipo, nombre
        LIMIT 100
    """)
    for row in rows:
        row["tipo"] = _tipo_amigable(row.get("tipo", ""))
    return rows


def _cargar_relaciones_incompletas():
    incompletas = []

    for doc in mongo_col("pilotos").find():
        node_id = _nodo_neo_para_doc("Piloto", doc)
        if not node_id:
            continue
        faltantes = []
        if not doc.get("equipo_id") and not _existe_relacion(node_id, "(n)-[:PERTENECE_A]->(:Equipo)"):
            faltantes.append("equipo")
        if not doc.get("vehiculo_id") and not _existe_relacion(node_id, "(n)-[:CONDUCE]->(:Vehiculo)"):
            faltantes.append("vehiculo")
        if not doc.get("copiloto_id") and not _existe_relacion(node_id, "(n)-[:TIENE_COPILOTO]-(:Copiloto)"):
            faltantes.append("copiloto")
        if faltantes:
            incompletas.append({"tipo": "Piloto", "nombre": _display_doc("Piloto", doc), "faltantes": faltantes})

    for doc in mongo_col("copiloto").find():
        node_id = _nodo_neo_para_doc("Copiloto", doc)
        if not node_id:
            continue
        faltantes = []
        if not doc.get("equipo_id") and not _existe_relacion(node_id, "(n)-[:PERTENECE_A]->(:Equipo)"):
            faltantes.append("equipo")
        if not doc.get("piloto_id") and not _existe_relacion(node_id, "(:Piloto)-[:TIENE_COPILOTO]-(n)"):
            faltantes.append("piloto")
        if faltantes:
            incompletas.append({"tipo": "Copiloto", "nombre": _display_doc("Copiloto", doc), "faltantes": faltantes})

    for doc in mongo_col("equipos").find():
        node_id = _nodo_neo_para_doc("Equipo", doc)
        if not node_id:
            continue
        faltantes = []
        if not doc.get("vehiculos_ids") and not _existe_relacion(node_id, "(n)-[:USA]->(:Vehiculo)"):
            faltantes.append("vehiculo")
        if not doc.get("patrocinadores_ids") and not _existe_relacion(node_id, "(:Patrocinador)-[:PATROCINA]->(n)"):
            faltantes.append("sponsor")
        if faltantes:
            incompletas.append({"tipo": "Equipo", "nombre": _display_doc("Equipo", doc), "faltantes": faltantes})

    return sorted(incompletas, key=lambda item: (item["tipo"], item["nombre"]))[:100]

    
# ─── Página principal ─────────────────────────────────────────────────────────

@ui.page("/static/neo4j")
def page_neo4j():
    ui.add_head_html(GLOBAL_CSS)
    ui.query("body").style(f"background:{DARK};")

    with ui.row().style("min-height:100vh; width:100%; gap:0;"):
        sidebar("/static/neo4j")

        with ui.column().classes("flex-1").style("padding:24px; overflow-y:auto;"):

            # Header
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().style("gap:2px;"):
                    ui.html(f'<div class="wrc-title" style="font-size:1.6rem;">NEO4J · RELACIONES</div>')
                    ui.html(f'<div class="wrc-label">Base de datos de grafos · '
                            f'<span style="color:{BLUE};">bolt://localhost:7687</span></div>')
                with ui.row().classes("gap-2"):
                    ui.button("↻  Refrescar", on_click=lambda: refrescar()).props("unelevated").style(
                        f"background:{CARD2}; color:{GREEN}; font-family:Courier New; font-weight:bold; "
                        f"border:1px solid {GREEN};"
                    )
                    ui.button("⬡  Crear relación", on_click=_dialogo_crear_relacion).props("unelevated").style(
                        f"background:{CARD2}; color:{BLUE}; font-family:Courier New; font-weight:bold; "
                        f"border:1px solid {BLUE};"
                    )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            tabla_contenedor = ui.column().classes("w-full")

            def refrescar():
                tabla_contenedor.clear()
                with tabla_contenedor:
                    try:
                        labels = _cargar_labels()
                        nodos_sueltos = _cargar_nodos_sueltos()
                        relaciones_incompletas = _cargar_relaciones_incompletas()
                        relaciones = _cargar_relaciones()
                    except Exception as e:
                        ui.notify(f"Error Neo4j: {e}", type="negative")
                        ui.label(str(e)).style(
                            f"font-family:'Courier New',monospace; color:{RED}; font-size:0.8rem;"
                        )
                        return

                    with ui.grid(columns=4).classes("w-full").style(
                        "gap:12px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));"
                    ):
                        if not labels:
                            ui.label("Sin nodos cargados.").style(
                                f"font-family:'Courier New',monospace; color:{GREY}; font-size:0.82rem;"
                            )
                        for item in labels:
                            with ui.column().style(
                                f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px; "
                                f"padding:12px; gap:4px;"
                            ):
                                ui.label(item.get("label", "-")).style(
                                    f"font-family:'Courier New',monospace; color:{BLUE}; "
                                    f"font-size:0.8rem; font-weight:bold;"
                                )
                                ui.label(str(item.get("cantidad", 0))).style(
                                    f"font-family:'Courier New',monospace; color:{WHITE}; "
                                    f"font-size:1.5rem; font-weight:bold;"
                                )

                    ui.html(f'<div class="section-label">AVISOS DE RELACIONES</div>')
                    with ui.grid(columns=2).classes("w-full").style(
                        "gap:12px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));"
                    ):
                        with ui.column().style(
                            f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px; "
                            f"padding:14px; gap:8px;"
                        ):
                            ui.label("Nodos sin ninguna relación").style(
                                f"font-family:'Courier New',monospace; color:{GOLD}; "
                                f"font-size:0.8rem; font-weight:bold;"
                            )
                            if not nodos_sueltos:
                                ui.label("No hay nodos sueltos.").style(
                                    f"font-family:'Courier New',monospace; color:{GREEN}; font-size:0.75rem;"
                                )
                            for item in nodos_sueltos[:8]:
                                ui.label(
                                    f'{item.get("tipo", "-")} · {item.get("nombre", "-")}'
                                ).style(
                                    f"font-family:'Courier New',monospace; color:{WHITE}; font-size:0.75rem;"
                                )

                        with ui.column().style(
                            f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px; "
                            f"padding:14px; gap:8px;"
                        ):
                            ui.label("Entidades con relaciones faltantes").style(
                                f"font-family:'Courier New',monospace; color:{GOLD}; "
                                f"font-size:0.8rem; font-weight:bold;"
                            )
                            if not relaciones_incompletas:
                                ui.label("No hay relaciones faltantes.").style(
                                    f"font-family:'Courier New',monospace; color:{GREEN}; font-size:0.75rem;"
                                )
                            for item in relaciones_incompletas[:8]:
                                faltantes = ", ".join(item.get("faltantes", []))
                                ui.label(
                                    f'{item.get("tipo", "-")} · {item.get("nombre", "-")} · falta: {faltantes}'
                                ).style(
                                    f"font-family:'Courier New',monospace; color:{WHITE}; font-size:0.75rem;"
                                )

                    ui.html(f'<div class="section-label">RELACIONES</div>')
                    columnas = [
                        {"name": "origen_tipo", "label": "ORIGEN TIPO", "field": "origen_tipo", "sortable": True, "align": "left", "style": f"color:{BLUE}; font-weight:bold;"},
                        {"name": "origen",      "label": "ORIGEN",      "field": "origen",      "sortable": True, "align": "left", "style": f"color:{WHITE}; font-weight:bold;"},
                        {"name": "relacion",    "label": "RELACIÓN",    "field": "relacion",    "sortable": True, "align": "center", "style": f"color:{GOLD}; font-weight:bold;"},
                        {"name": "destino_tipo","label": "DESTINO TIPO","field": "destino_tipo","sortable": True, "align": "left", "style": f"color:{BLUE}; font-weight:bold;"},
                        {"name": "destino",     "label": "DESTINO",     "field": "destino",     "sortable": True, "align": "left", "style": f"color:{WHITE}; font-weight:bold;"},
                    ]
                    ui.table(columns=columnas, rows=relaciones, row_key="origen").style(
                        f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px; width:100%;"
                    ).props("flat dark")

            refrescar()
