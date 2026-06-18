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
(t1:Temporada {nombre: "Temporada WRC 2026", anio: 2026}),
(c1:Campeonato {nombre: "World Rally Cup", organizador: "FIA"}),
(r1:Rally {nombre: "Rally Finland", pais: "Finlandia"}),
(e1:Equipo {nombre: "Monster Rally Team", pais: "Estados Unidos"}),
(e2:Equipo {nombre: "Andes Motorsport", pais: "Argentina"}),
(e3:Equipo {nombre: "Samurai Racing", pais: "Japón"}),
(p1:Piloto {nombre: "Luca Moretti", pais: "Italia", edad: 28}),
(p2:Piloto {nombre: "Carlos Benítez", pais: "Argentina", edad: 31}),
(p3:Piloto {nombre: "Hiro Tanaka", pais: "Japón", edad: 26}),
(co1:Copiloto {nombre: "Marco Bellini", pais: "Italia", edad: 30}),
(co2:Copiloto {nombre: "Diego Suárez", pais: "Argentina", edad: 29}),
(co3:Copiloto {nombre: "Yuki Nakamura", pais: "Japón", edad: 27}),
(j1:JefeIngenieria {nombre: "Michael Ross", especialidad: "Motores", experiencia: 12}),
(j2:JefeIngenieria {nombre: "Santiago Rivas", especialidad: "Suspensión", experiencia: 8}),
(j3:JefeIngenieria {nombre: "Kenji Sato", especialidad: "Aerodinámica", experiencia: 10}),
(v1:Vehiculo {modelo: "Ford Puma Rally1", hp: 500, velocidad_maxima: 210}),
(v2:Vehiculo {modelo: "Ford Fiesta Rally2", hp: 470, velocidad_maxima: 205}),
(v3:Vehiculo {modelo: "Toyota GR Yaris Rally1", hp: 520, velocidad_maxima: 215}),
(v4:Vehiculo {modelo: "Toyota Corolla Rally2", hp: 480, velocidad_maxima: 208}),
(v5:Vehiculo {modelo: "Hyundai i20 N Rally1", hp: 510, velocidad_maxima: 212}),
(v6:Vehiculo {modelo: "Hyundai i20 Rally2", hp: 475, velocidad_maxima: 206}),
(s1:Patrocinador {nombre: "RedBull", industria: "Bebidas energéticas"}),
(s2:Patrocinador {nombre: "Pirelli", industria: "Neumáticos"}),
(s3:Patrocinador {nombre: "Shell", industria: "Combustibles"}),

(t1)-[:TIENE_CAMPEONATO]->(c1),
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
