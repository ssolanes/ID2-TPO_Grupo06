# frontend_static/shared.py
# Conexiones a MongoDB y Neo4j + estilos compartidos

from pymongo import MongoClient
from neo4j import GraphDatabase
from bson import ObjectId

# ─── MongoDB ────────────────────────────────────────────────────────────────
_mongo_client = None

def get_mongo_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    return _mongo_client["mundial_rally"]

def mongo_col(nombre: str):
    return get_mongo_db()[nombre]

def get_query_id(doc_id: str):
    try:
        if ObjectId.is_valid(doc_id):
            return ObjectId(doc_id)
    except Exception:
        pass
    return doc_id

# ─── Neo4j ───────────────────────────────────────────────────────────────────
_neo4j_driver = None

def get_neo4j():
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "12345678")   # <─ cambiá la contraseña si es distinta
        )
    return _neo4j_driver

def neo4j_query(cypher: str, params: dict = None):
    driver = get_neo4j()
    with driver.session() as session:
        result = session.run(cypher, params or {})
        return [dict(r) for r in result]


# ─── Sincronizacion MongoDB → Neo4j ──────────────────────────────────────────

ENTIDADES_NEO = {
    "Piloto": {
        "coleccion": "pilotos",
        "label": "Piloto",
        "prop_nombre": "nombre",
    },
    "Copiloto": {
        "coleccion": "copiloto",
        "label": "Copiloto",
        "prop_nombre": "nombre",
    },
    "Equipo": {
        "coleccion": "equipos",
        "label": "Equipo",
        "prop_nombre": "nombre",
    },
    "Vehiculo": {
        "coleccion": "vehiculos",
        "label": "Vehiculo",
        "prop_nombre": "modelo",
    },
    "Patrocinador": {
        "coleccion": "patrocinador",
        "label": "Patrocinador",
        "prop_nombre": "nombre",
    },
    "JefeIngenieria": {
        "coleccion": "jefe_ingenieria",
        "label": "JefeIngenieria",
        "prop_nombre": "nombre",
    },
    "Rally": {
        "coleccion": "rallies",
        "label": "Rally",
        "prop_nombre": "nombre",
    },
    "NoticiaReporte": {
        "coleccion": "noticias_reportes",
        "label": "NoticiaReporte",
        "prop_nombre": "titular",
    },
    "ResumenCarrera": {
        "coleccion": "resumenes_carrera",
        "label": "ResumenCarrera",
        "prop_nombre": "titulo",
    },
}


def _nombre_completo(doc: dict) -> str:
    return f'{doc.get("nombre", "")} {doc.get("apellido", "")}'.strip()


def display_doc_neo(tipo: str, doc: dict) -> str:
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


ALIAS_VISUALES_NEO = {
    "Vehiculo": "modelo",
    "NoticiaReporte": "titular",
    "ResumenCarrera": "titulo",
}


def props_neo_desde_mongo(tipo: str, doc: dict) -> dict:
    nombre = display_doc_neo(tipo, doc)
    props = {
        "mongo_id": str(doc.get("_id", "")),
        "nombre": nombre,
    }
    alias = ALIAS_VISUALES_NEO.get(tipo)
    if alias:
        props[alias] = nombre
    return props


def sync_neo_node_from_doc(tipo: str, doc_id: str):
    meta = ENTIDADES_NEO[tipo]
    doc = mongo_col(meta["coleccion"]).find_one({"_id": get_query_id(str(doc_id))})
    if not doc:
        return False

    label = meta["label"]
    props = props_neo_desde_mongo(tipo, doc)

    neo4j_query(f"""
        MERGE (n:{label} {{mongo_id: $mongo_id}})
        SET n = $props
        RETURN elementId(n) AS id
    """, {
        "mongo_id": props["mongo_id"],
        "props": props,
    })
    return True


def delete_neo_node_from_doc(tipo: str, doc_id: str):
    meta = ENTIDADES_NEO[tipo]
    neo4j_query(f"""
        MATCH (n:{meta["label"]} {{mongo_id: $mongo_id}})
        DETACH DELETE n
    """, {"mongo_id": str(doc_id)})

# ─── Paleta WRC ──────────────────────────────────────────────────────────────
RED    = "#E8002A"
GOLD   = "#F5C518"
BLUE   = "#0080FF"
GREEN  = "#00D97E"
DARK   = "#0A0A0C"
PANEL  = "#111116"
CARD   = "#16161D"
CARD2  = "#1C1C24"
WHITE  = "#F0F0F0"
GREY   = "#8A8A9A"
BORDER = "#2A2A38"

# CSS global inyectado en cada página
GLOBAL_CSS = f"""
<style>
  body, .nicegui-content {{ background: {DARK} !important; }}
  .wrc-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 16px;
  }}
  .wrc-card2 {{
    background: {CARD2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 12px;
  }}
  .wrc-title {{
    font-family: 'Courier New', monospace;
    font-weight: bold;
    color: {WHITE};
  }}
  .wrc-label {{
    font-family: 'Courier New', monospace;
    color: {GREY};
    font-size: 0.85rem;
  }}
  .wrc-value {{
    font-family: 'Courier New', monospace;
    color: {WHITE};
    font-weight: bold;
  }}
  .wrc-accent {{ color: {RED}; }}
  .wrc-gold   {{ color: {GOLD}; }}
  .wrc-green  {{ color: {GREEN}; }}
  .wrc-blue   {{ color: {BLUE}; }}
  .badge-green {{
    background: #002918; border: 1px solid #004D2E;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {GREEN};
  }}
  .badge-red {{
    background: #2D0009; border: 1px solid #4A000F;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {RED};
  }}
  .badge-gold {{
    background: #2D2400; border: 1px solid #4A3A00;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {GOLD};
  }}
  .badge-blue {{
    background: #001A33; border: 1px solid #003366;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem; font-weight: bold; color: {BLUE};
  }}
  .nav-link {{
    font-family: 'Courier New', monospace;
    color: {GREY}; text-decoration: none;
    padding: 8px 16px; border-radius: 6px;
    transition: background 0.2s;
  }}
  .nav-link:hover {{ background: {CARD2}; color: {WHITE}; }}
  .nav-active {{
    background: {CARD2}; color: {WHITE} !important;
    border-left: 3px solid {RED};
  }}
  .section-label {{
    font-family: 'Courier New', monospace;
    font-size: 0.75rem; font-weight: bold;
    color: {RED}; letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 16px 0 8px 0;
  }}
  .code-block {{
    background: {CARD2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 14px;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    color: {GREEN};
    white-space: pre;
    overflow-x: auto;
  }}
  .q-table {{ background: {CARD} !important; }}
  .q-table thead tr {{ background: {CARD2} !important; }}
  .q-table tbody tr:hover {{ background: {CARD2} !important; }}
  .q-table th, .q-table td {{
    font-family: 'Courier New', monospace !important;
    color: {WHITE} !important;
    border-color: {BORDER} !important;
  }}
</style>
"""

def sidebar(pagina_actual: str):
    """Barra lateral de navegación compartida."""
    from nicegui import ui

    items = [
        ("/static/pilotos",        "◉  Pilotos"),
        ("/static/copilotos",      "○  Copilotos"),
        ("/static/jefes_ingenieria","⚙  Jefes Ingeniería"),
        ("/static/equipos",        "◈  Equipos"),
        ("/static/vehiculos",      "⛍  Vehículos"),
        ("/static/patrocinadores", "◇  Patrocinadores"),
        ("/static/rallies",        "◎  Rallies / Etapas"),
        ("/static/resumenes_carrera", "🏁 Resúmenes Carrera"),
        ("/static/noticias_reportes", "📰 Noticias / Reportes"),
        ("/static/neo4j",          "⬡  Neo4j · Relaciones"),
    ]

    with ui.column().classes("h-full").style(
        f"width:220px; min-height:100vh; background:{PANEL}; "
        f"border-right:1px solid {BORDER}; padding:0; flex-shrink:0;"
    ):
        # Logo
        with ui.element("div").style(
            f"background:{CARD2}; padding:18px 16px; "
            f"border-bottom:1px solid {BORDER};"
        ):
            ui.html(
                f'<a href="http://localhost:8080" '
                f'style="text-decoration:none; display:block;">'
                f'<span style="font-family:Courier New;font-size:1.6rem;'
                f'font-weight:bold;color:{RED};">WRC</span>'
                f'<span style="font-family:Courier New;font-size:0.75rem;'
                f'color:{GREY};display:block;margin-top:2px;">Static Data · CRUD</span>'
                f'</a>'
            )

        ui.separator().style(f"background:{BORDER}; margin:0;")

        ui.html(f'<div class="section-label" style="padding:0 16px;">MongoDB · Neo4j</div>')

        for ruta, label in items:
            activo = pagina_actual == ruta
            clase = "nav-link nav-active" if activo else "nav-link"
            ui.html(
                f'<a href="{ruta}" class="{clase}" '
                f'style="display:block; margin:2px 8px;">{label}</a>'
            )

        # Footer
        with ui.element("div").style(
            f"position:absolute; bottom:0; width:220px; padding:12px 16px; "
            f"border-top:1px solid {BORDER}; background:{PANEL};"
        ):
            ui.html(
                f'<div style="font-family:Courier New;font-size:0.7rem;'
                f'color:{GREY};text-align:center;">'
                f'FIA · Temporada 2026<br>'
                f'<span style="color:{BORDER};">MongoDB · Neo4j</span></div>'
            )
