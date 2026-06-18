from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError


URI = "bolt://localhost:7687"
# Para que les ande tienen que crear una instancia de neo4j con estos datos y correrla
USER = "neo4j" 
PASSWORD = "12345678"

try:
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
except ServiceUnavailable:
    print("La instancia de Neo4j no esta corriendo")
    exit(1)
except AuthError:
    print("Usuario o contraseña incorrectos")
    exit(1)

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

cypher = """
CREATE
(c1:Campeonato {mongo_id: "campeonato_wrc", nombre: "World Rally Cup"}),
(r1:Rally {mongo_id: "rally_fin_2026", nombre: "Rally Finland"}),
(e1:Equipo {mongo_id: "eq_monster", nombre: "Monster Rally Team"}),
(e2:Equipo {mongo_id: "eq_andes", nombre: "Andes Motorsport"}),
(e3:Equipo {mongo_id: "eq_samurai", nombre: "Samurai Racing"}),
(p1:Piloto {mongo_id: "piloto_moretti", nombre: "Luca Moretti"}),
(p2:Piloto {mongo_id: "piloto_benitez", nombre: "Carlos Benítez"}),
(p3:Piloto {mongo_id: "piloto_tanaka", nombre: "Hiro Tanaka"}),
(co1:Copiloto {mongo_id: "copiloto_bellini", nombre: "Marco Bellini"}),
(co2:Copiloto {mongo_id: "copiloto_suarez", nombre: "Diego Suárez"}),
(co3:Copiloto {mongo_id: "copiloto_nakamura", nombre: "Yuki Nakamura"}),
(j1:JefeIngenieria {mongo_id: "ji_ross", nombre: "Michael Ross"}),
(j2:JefeIngenieria {mongo_id: "ji_rivas", nombre: "Santiago Rivas"}),
(j3:JefeIngenieria {mongo_id: "ji_sato", nombre: "Kenji Sato"}),
(v1:Vehiculo {mongo_id: "veh_puma_r1", nombre: "Ford Puma Rally1"}),
(v2:Vehiculo {mongo_id: "veh_fiesta_r2", nombre: "Ford Fiesta Rally2"}),
(v3:Vehiculo {mongo_id: "veh_yaris_r1", nombre: "Toyota GR Yaris Rally1"}),
(v4:Vehiculo {mongo_id: "veh_corolla_r2", nombre: "Toyota Corolla Rally2"}),
(v5:Vehiculo {mongo_id: "veh_i20_r1", nombre: "Hyundai i20 N Rally1"}),
(v6:Vehiculo {mongo_id: "veh_i20_r2", nombre: "Hyundai i20 Rally2"}),
(s1:Patrocinador {mongo_id: "sponsor_redbull", nombre: "RedBull"}),
(s2:Patrocinador {mongo_id: "sponsor_pirelli", nombre: "Pirelli"}),
(s3:Patrocinador {mongo_id: "sponsor_shell", nombre: "Shell"}),

(c1)-[:TIENE_RALLY]->(r1),

(p1)-[:PERTENECE_A]->(e1),
(p2)-[:PERTENECE_A]->(e2),
(p3)-[:PERTENECE_A]->(e3),
(co1)-[:PERTENECE_A]->(e1),
(co2)-[:PERTENECE_A]->(e2),
(co3)-[:PERTENECE_A]->(e3),

(j1)-[:DIRIGE]->(e1),
(j2)-[:DIRIGE]->(e2),
(j3)-[:DIRIGE]->(e3),

(e1)-[:USA]->(v1),
(e1)-[:USA]->(v2),
(e2)-[:USA]->(v3),
(e2)-[:USA]->(v4),
(e3)-[:USA]->(v5),
(e3)-[:USA]->(v6),

(p1)-[:CONDUCE]->(v1),
(p2)-[:CONDUCE]->(v3),
(p3)-[:CONDUCE]->(v5),

(co1)-[:ASISTE_EN]->(v1),
(co2)-[:ASISTE_EN]->(v3),
(co3)-[:ASISTE_EN]->(v5),

(p1)-[:PARTICIPA_EN]->(r1),
(p2)-[:PARTICIPA_EN]->(r1),
(p3)-[:PARTICIPA_EN]->(r1),
(co1)-[:PARTICIPA_EN]->(r1),
(co2)-[:PARTICIPA_EN]->(r1),
(co3)-[:PARTICIPA_EN]->(r1),

(s1)-[:PATROCINA]->(e1),
(s2)-[:PATROCINA]->(e2),
(s3)-[:PATROCINA]->(e3)
"""

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")
    session.run(cypher)

    result = session.run("MATCH (n) RETURN count(n) AS cantidad")
    cantidad = result.single()["cantidad"]

    print(f"Base de Neo4j reiniciada y datos cargados correctamente.")
    print(f"Nodos cargados: {cantidad}")

driver.close()
