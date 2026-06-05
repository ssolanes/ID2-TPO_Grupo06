from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

cypher = """
CREATE
(t1:Temporada {nombre: "Temporada WRC 2026", anio: 2026}),
(c1:Campeonato {nombre: "World Rally Cup", organizador: "FIA"}),
(r1:Rally {nombre: "Rally Finland", pais: "Finlandia"}),
(l1:Leg {nombre: "Leg 1", dia: "Viernes"}),
(l2:Leg {nombre: "Leg 2", dia: "Sábado"}),
(l3:Leg {nombre: "Leg 3", dia: "Domingo"}),
(ss1:SpecialStage {nombre: "SS1", kilometros: 12.5}),
(ss2:SpecialStage {nombre: "SS2", kilometros: 18.3}),
(ss3:SpecialStage {nombre: "SS3", kilometros: 15.1}),
(ss4:SpecialStage {nombre: "SS4", kilometros: 21.4}),
(ss5:SpecialStage {nombre: "SS5", kilometros: 16.8}),
(ss6:SpecialStage {nombre: "SS6", kilometros: 19.2}),
(ss7:SpecialStage {nombre: "SS7", kilometros: 14.7}),
(ss8:SpecialStage {nombre: "Power Stage", kilometros: 10.9, puntos_extra: true}),
(sp1:Split {nombre: "Split 1"}),
(sp2:Split {nombre: "Split 2"}),
(sp3:Split {nombre: "Split 3"}),
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
(f1:FallaMecanica {tipo: "Motor", gravedad: "Alta"}),
(f2:FallaMecanica {tipo: "Suspensión", gravedad: "Media"}),
(f3:FallaMecanica {tipo: "Frenos", gravedad: "Alta"}),
(s1:Patrocinador {nombre: "RedBull", industria: "Bebidas energéticas"}),
(s2:Patrocinador {nombre: "Pirelli", industria: "Neumáticos"}),
(s3:Patrocinador {nombre: "Shell", industria: "Combustibles"}),

(t1)-[:TIENE_CAMPEONATO]->(c1),
(c1)-[:TIENE_RALLY]->(r1),
(r1)-[:TIENE_LEG]->(l1),
(r1)-[:TIENE_LEG]->(l2),
(r1)-[:TIENE_LEG]->(l3),
(l1)-[:TIENE_SS]->(ss1),
(l1)-[:TIENE_SS]->(ss2),
(l1)-[:TIENE_SS]->(ss3),
(l2)-[:TIENE_SS]->(ss4),
(l2)-[:TIENE_SS]->(ss5),
(l2)-[:TIENE_SS]->(ss6),
(l3)-[:TIENE_SS]->(ss7),
(l3)-[:TIENE_SS]->(ss8),
(ss1)-[:TIENE_SPLIT]->(sp1),
(ss1)-[:TIENE_SPLIT]->(sp2),
(ss1)-[:TIENE_SPLIT]->(sp3),

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

(p1)-[:PARTICIPA_EN]->(c1),
(p2)-[:PARTICIPA_EN]->(c1),
(p3)-[:PARTICIPA_EN]->(c1),
(co1)-[:PARTICIPA_EN]->(c1),
(co2)-[:PARTICIPA_EN]->(c1),
(co3)-[:PARTICIPA_EN]->(c1),

(p1)-[:CORRE_EN]->(ss1),
(p2)-[:CORRE_EN]->(ss1),
(p3)-[:CORRE_EN]->(ss1),
(co1)-[:CORRE_EN]->(ss1),
(co2)-[:CORRE_EN]->(ss1),
(co3)-[:CORRE_EN]->(ss1),

(v1)-[:COMPITE_EN]->(ss1),
(v3)-[:COMPITE_EN]->(ss1),
(v5)-[:COMPITE_EN]->(ss1),

(v1)-[:TIENE_FALLA]->(f1),
(v3)-[:TIENE_FALLA]->(f2),
(v5)-[:TIENE_FALLA]->(f3),

(s1)-[:PATROCINA]->(e1),
(s2)-[:PATROCINA]->(e2),
(s3)-[:PATROCINA]->(e3)
"""

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")
    session.run(cypher)

    result = session.run("MATCH (n) RETURN count(n) AS cantidad")
    cantidad = result.single()["cantidad"]

    print(f"Base reiniciada y datos cargados correctamente.")
    print(f"Nodos cargados: {cantidad}")

driver.close()