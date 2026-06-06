# frontend_static/pages/neo4j_relaciones.py
# Visualización de relaciones · Neo4j

from nicegui import ui
from frontend_static.shared import (
    get_neo4j, neo4j_query, sidebar, GLOBAL_CSS,
    RED, GOLD, GREEN, BLUE, GREY, CARD, CARD2, BORDER, WHITE, DARK
)

# CRUD (hay que modificarlo)

def _dialogo_crear_nodo():
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:480px;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{RED};">＋  Crear Nodo Neo4j</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")
        ui.html(f'<div class="section-label">TIPO DE NODO</div>')

        inp_tipo = ui.select(
            ["Piloto","Equipo","Patrocinador","Ingeniero","Vehiculo","Campeonato"],
            value="Piloto", label="Etiqueta (Label)"
        ).props("outlined dark dense").classes("w-full")

        ui.html(f'<div class="section-label">PROPIEDADES (formato: clave: valor, una por línea)</div>')
        inp_props = ui.textarea(
            placeholder="nombre: Sébastien Ogier\nnacionalidad: FR\nnumero: 1",
        ).style(
            f"width:100%; font-family:Courier New; font-size:0.82rem; "
            f"background:{CARD2}; color:{GREEN}; border:1px solid {BORDER}; "
            f"border-radius:6px; padding:10px; min-height:120px;"
        ).props("outlined dark")

        resultado = ui.html("")

        def crear():
            props_dict = {}
            for linea in inp_props.value.strip().splitlines():
                if ":" in linea:
                    k, v = linea.split(":", 1)
                    props_dict[k.strip()] = v.strip()

            if not props_dict:
                ui.notify("Ingresá al menos una propiedad", type="warning")
                return

            props_str = ", ".join(f'n.{k} = ${k}' for k in props_dict)
            cypher = f"CREATE (n:{inp_tipo.value}) SET {props_str} RETURN n"
            try:
                neo4j_query(cypher, props_dict)
                ui.notify(f"Nodo {inp_tipo.value} creado ✓", type="positive")
                resultado.set_content(
                    f'<div style="font-family:Courier New;color:{GREEN};font-size:0.82rem;">'
                    f'✓ Nodo creado: ({inp_tipo.value} {{{", ".join(f"{k}: {v}" for k,v in props_dict.items())}}})</div>'
                )
            except Exception as e:
                ui.notify(f"Error Neo4j: {e}", type="negative")

        ui.separator().style(f"background:{BORDER}; margin:8px 0;")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat").style(f"color:{GREY};")
            ui.button("Crear nodo", on_click=crear).props("unelevated").style(
                f"background:{BLUE}; color:white; font-family:Courier New; font-weight:bold;"
            )
    dlg.open()


def _dialogo_crear_relacion():
    with ui.dialog().props("persistent") as dlg, \
         ui.card().style(f"background:{CARD}; border:1px solid {BORDER}; min-width:520px;"):

        with ui.row().classes("w-full items-center justify-between"):
            ui.html(f'<span style="font-family:Courier New;font-size:1.1rem;font-weight:bold;color:{BLUE};">⬡  Crear Relación Neo4j</span>')
            ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(f"color:{GREY};")

        ui.separator().style(f"background:{BORDER};")

        def lbl(t): ui.html(f'<div class="section-label">{t}</div>')

        lbl("NODO ORIGEN")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_label_a = ui.select(["Piloto","Equipo","Patrocinador","Ingeniero","Vehiculo"], value="Piloto", label="Label").props("outlined dark dense")
            inp_prop_a  = ui.input("Propiedad buscada (ej: nombre)", value="nombre").props("outlined dark dense")
            inp_val_a   = ui.input("Valor (ej: Sébastien Ogier)").props("outlined dark dense")

        lbl("NODO DESTINO")
        with ui.grid(columns=2).classes("w-full gap-2"):
            inp_label_b = ui.select(["Piloto","Equipo","Patrocinador","Ingeniero","Vehiculo"], value="Equipo", label="Label").props("outlined dark dense")
            inp_prop_b  = ui.input("Propiedad buscada", value="nombre").props("outlined dark dense")
            inp_val_b   = ui.input("Valor").props("outlined dark dense")

        lbl("TIPO DE RELACIÓN")
        inp_rel = ui.select(
            ["CONDUCE_PARA","CONDUJO_PARA","PATROCINA","TRABAJA_EN","PERTENECE_A","PARTICIPA_EN"],
            value="CONDUCE_PARA", label="Relación"
        ).props("outlined dark dense").classes("w-full")

        lbl("PROPIEDADES DE LA RELACIÓN (opcional, formato: clave: valor)")
        inp_rel_props = ui.input(placeholder="temporada: 2026").props("outlined dark dense").classes("w-full")

        resultado = ui.html("")

        def crear():
            rel_props = {}
            if inp_rel_props.value.strip():
                for linea in inp_rel_props.value.strip().splitlines():
                    if ":" in linea:
                        k, v = linea.split(":", 1)
                        rel_props[k.strip()] = v.strip()

            rel_set = ""
            if rel_props:
                rel_set = " SET " + ", ".join(f'r.{k} = "{v}"' for k,v in rel_props.items())

            cypher = (
                f"MATCH (a:{inp_label_a.value} {{{inp_prop_a.value}: $val_a}}), "
                f"(b:{inp_label_b.value} {{{inp_prop_b.value}: $val_b}}) "
                f"CREATE (a)-[r:{inp_rel.value}]->(b){rel_set} RETURN r"
            )
            try:
                neo4j_query(cypher, {"val_a": inp_val_a.value, "val_b": inp_val_b.value})
                ui.notify(f"Relación {inp_rel.value} creada ✓", type="positive")
                resultado.set_content(
                    f'<div style="font-family:Courier New;color:{GREEN};font-size:0.82rem;">'
                    f'✓ ({inp_label_a.value})-[:{inp_rel.value}]->({inp_label_b.value})</div>'
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
                    ui.button("＋  Crear nodo", on_click=_dialogo_crear_nodo).props("unelevated").style(
                        f"background:{BLUE}; color:white; font-family:Courier New; font-weight:bold;"
                    )
                    ui.button("⬡  Crear relación", on_click=_dialogo_crear_relacion).props("unelevated").style(
                        f"background:{CARD2}; color:{BLUE}; font-family:Courier New; font-weight:bold; "
                        f"border:1px solid {BLUE};"
                    )

            ui.separator().style(f"background:{BORDER}; margin:8px 0 16px 0;")

            tabla_contenedor = ui.column().classes("w-full")
           



