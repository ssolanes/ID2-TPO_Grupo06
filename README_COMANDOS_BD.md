# Comandos PowerShell para consultar las bases de datos

Referencia rápida del proyecto World Rally Cup. Los comandos están preparados para los contenedores actuales:

- `mongodb`
- `neo4j`
- `redis`
- `cassandra`

> Los ejemplos son de consulta y no eliminan información.

---

## 1. Docker

### Ver contenedores activos

```powershell
docker ps
```

### Ver únicamente las cuatro bases

```powershell
docker ps --filter name=mongodb --filter name=neo4j --filter name=redis --filter name=cassandra
```

### Iniciar las cuatro bases

```powershell
docker start mongodb neo4j redis cassandra
```

### Ver los últimos logs

```powershell
docker logs --tail 50 mongodb
docker logs --tail 50 neo4j
docker logs --tail 50 redis
docker logs --tail 50 cassandra
```

### Seguir logs en vivo

```powershell
docker logs -f cassandra
```

Para dejar de seguirlos, presionar `Ctrl+C`.

---

## 2. MongoDB

La base utilizada por el proyecto es `mundial_rally`.

### Abrir la consola interactiva

```powershell
docker exec -it mongodb mongosh mundial_rally
```

### Listar bases de datos

```powershell
docker exec mongodb mongosh --quiet --eval "db.adminCommand({listDatabases:1}).databases.forEach(d => print(d.name))"
```

### Listar colecciones

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.getCollectionNames().forEach(print)"
```

### Mostrar documentos de una colección

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.pilotos.find().limit(10).forEach(printjson)"
```

Se puede reemplazar `pilotos` por:

```text
campeonatos
equipos
copiloto
jefe_ingenieria
vehiculos
rallies
patrocinador
resumenes_carrera
noticias_reportes
```

### Buscar documentos por un campo

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.pilotos.find({estado:'activo'}).forEach(printjson)"
```

### Consultar un campo anidado

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.pilotos.find({'estadisticas.puntos':{`$gt:100}}).forEach(printjson)"
```

En PowerShell se escapa el signo `$` como `` `$ ``.

### Mostrar únicamente campos determinados

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.pilotos.find({}, {nombre:1, apellido:1, _id:0}).limit(20).forEach(printjson)"
```

### Ordenar resultados

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.pilotos.find().sort({'estadisticas.puntos':-1}).limit(10).forEach(printjson)"
```

### Contar documentos de una colección

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.pilotos.countDocuments({})"
```

### Contar documentos en todas las colecciones

```powershell
docker exec mongodb mongosh mundial_rally --quiet --eval "db.getCollectionNames().forEach(c => print(c, db.getCollection(c).countDocuments({})))"
```

---

## 3. Neo4j

### Abrir la consola interactiva

```powershell
docker exec -it neo4j cypher-shell -u neo4j -p 12345678
```

### Mostrar nodos

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (n) RETURN n LIMIT 20"
```

### Contar todos los nodos

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (n) RETURN count(n) AS total"
```

### Contar nodos por etiqueta

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (n) UNWIND labels(n) AS etiqueta RETURN etiqueta, count(*) AS cantidad ORDER BY etiqueta"
```

### Mostrar relaciones

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (a)-[r]->(b) RETURN coalesce(a.nombre,a.modelo,a.titulo,a.titular) AS origen, type(r) AS relacion, coalesce(b.nombre,b.modelo,b.titulo,b.titular) AS destino LIMIT 30"
```

### Contar relaciones por tipo

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH ()-[r]->() RETURN type(r) AS tipo, count(r) AS cantidad ORDER BY tipo"
```

### Consultar pilotos y equipos

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (p:Piloto)-[:PERTENECE_A]->(e:Equipo) RETURN p.nombre AS piloto, e.nombre AS equipo LIMIT 20"
```

### Consultar pilotos y vehículos

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (p:Piloto)-[:CONDUCE]->(v:Vehiculo) RETURN p.nombre AS piloto, v.modelo AS vehiculo LIMIT 20"
```

### Consultar participantes de un rally

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (p)-[:PARTICIPA_EN]->(r:Rally) RETURN labels(p)[0] AS tipo, p.nombre AS participante, r.nombre AS rally LIMIT 30"
```

### Encontrar nodos aislados

```powershell
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (n) WHERE NOT (n)--() RETURN labels(n) AS tipo, coalesce(n.nombre,n.modelo,n.titulo,n.titular) AS nombre LIMIT 30"
```

Neo4j Browser está disponible en:

```text
http://localhost:7474
```

---

## 4. Redis

### Abrir la consola interactiva

```powershell
docker exec -it redis redis-cli
```

### Verificar conexión

```powershell
docker exec redis redis-cli PING
```

Resultado esperado:

```text
PONG
```

### Listar claves de la carrera

```powershell
docker exec redis redis-cli --scan --pattern "carrera:wrc_2026_finlandia:*"
```

Es preferible `SCAN` antes que `KEYS *`, porque no bloquea Redis.

### Consultar el piloto activo

```powershell
docker exec redis redis-cli GET carrera:wrc_2026_finlandia:piloto:activo
```

### Consultar el próximo piloto

```powershell
docker exec redis redis-cli GET carrera:wrc_2026_finlandia:piloto:siguiente
```

### Consultar el auto y la telemetría actual

```powershell
docker exec redis redis-cli HGETALL carrera:wrc_2026_finlandia:auto:activo
```

### Consultar el ranking vivo

```powershell
docker exec redis redis-cli ZRANGE carrera:wrc_2026_finlandia:ranking:vivo 0 -1 WITHSCORES
```

### Consultar el ranking de referencia

```powershell
docker exec redis redis-cli ZRANGE carrera:wrc_2026_finlandia:ranking:referencia 0 -1 WITHSCORES
```

### Consultar usuarios activos

```powershell
docker exec redis redis-cli SMEMBERS carrera:wrc_2026_finlandia:usuarios:activos
```

### Mostrar los primeros eventos del Stream

```powershell
docker exec redis redis-cli XRANGE carrera:wrc_2026_finlandia:eventos - + COUNT 10
```

### Mostrar los eventos más recientes

```powershell
docker exec redis redis-cli XREVRANGE carrera:wrc_2026_finlandia:eventos + - COUNT 10
```

### Contar eventos del Stream

```powershell
docker exec redis redis-cli XLEN carrera:wrc_2026_finlandia:eventos
```

### Consultar el tipo de una clave

```powershell
docker exec redis redis-cli TYPE carrera:wrc_2026_finlandia:auto:activo
```

### Contar todas las claves

```powershell
docker exec redis redis-cli DBSIZE
```

---

## 5. Cassandra

El keyspace utilizado por el proyecto es `world_rally_cup`.

### Abrir la consola interactiva

```powershell
docker exec -it cassandra cqlsh
```

### Verificar conexión

```powershell
docker exec cassandra cqlsh -e "SELECT cluster_name FROM system.local;"
```

### Listar keyspaces

```powershell
docker exec cassandra cqlsh -e "DESCRIBE KEYSPACES;"
```

### Mostrar la estructura del keyspace

```powershell
docker exec cassandra cqlsh -e "DESCRIBE KEYSPACE world_rally_cup;"
```

### Listar sus tablas

```powershell
docker exec cassandra cqlsh -e "USE world_rally_cup; DESCRIBE TABLES;"
```

### Consultar telemetría de un piloto

```powershell
docker exec cassandra cqlsh -e "SELECT * FROM world_rally_cup.telemetria_historica WHERE carrera='wrc_2026_finlandia' AND piloto='p1' LIMIT 10;"
```

### Consultar tiempos de un checkpoint

```powershell
docker exec cassandra cqlsh -e "SELECT * FROM world_rally_cup.tiempos_checkpoint WHERE carrera='wrc_2026_finlandia' AND checkpoint=1 LIMIT 10;"
```

### Consultar el ranking histórico

```powershell
docker exec cassandra cqlsh -e "SELECT * FROM world_rally_cup.ranking_temporal WHERE carrera='wrc_2026_finlandia' LIMIT 10;"
```

### Consultar eventos históricos

```powershell
docker exec cassandra cqlsh -e "SELECT * FROM world_rally_cup.eventos_carrera WHERE carrera='wrc_2026_finlandia' LIMIT 10;"
```

### Consultar las cuatro tablas en un comando

```powershell
docker exec cassandra cqlsh -e "SELECT * FROM world_rally_cup.telemetria_historica LIMIT 10; SELECT * FROM world_rally_cup.tiempos_checkpoint LIMIT 10; SELECT * FROM world_rally_cup.ranking_temporal LIMIT 10; SELECT * FROM world_rally_cup.eventos_carrera LIMIT 10;"
```

### Contar filas de las cuatro tablas

```powershell
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM world_rally_cup.telemetria_historica; SELECT COUNT(*) FROM world_rally_cup.tiempos_checkpoint; SELECT COUNT(*) FROM world_rally_cup.ranking_temporal; SELECT COUNT(*) FROM world_rally_cup.eventos_carrera;"
```

Los `COUNT(*)` completos pueden resultar costosos cuando las tablas tienen muchos registros.

---

## 6. Aplicación

### Ejecutar el proyecto

```powershell
python run.py
```

La consola queda ocupada mientras el servidor está activo. Esto es normal.

### Verificar los puertos

```powershell
Test-NetConnection localhost -Port 8080
Test-NetConnection localhost -Port 8081
Test-NetConnection localhost -Port 8082
```

### Comprobar respuestas HTTP

```powershell
Invoke-WebRequest http://localhost:8080 -UseBasicParsing
Invoke-WebRequest http://localhost:8081 -UseBasicParsing
Invoke-WebRequest http://localhost:8082 -UseBasicParsing
```

### Direcciones

```text
http://localhost:8080  Selector principal
http://localhost:8081  MongoDB + Neo4j
http://localhost:8082  Redis + Cassandra
```

---

## 7. Resumen rápido

```powershell
# MongoDB: documentos de pilotos
docker exec mongodb mongosh mundial_rally --quiet --eval "db.pilotos.find().limit(10).forEach(printjson)"

# Neo4j: relaciones
docker exec neo4j cypher-shell -u neo4j -p 12345678 "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10"

# Redis: auto activo
docker exec redis redis-cli HGETALL carrera:wrc_2026_finlandia:auto:activo

# Cassandra: eventos históricos
docker exec cassandra cqlsh -e "SELECT * FROM world_rally_cup.eventos_carrera WHERE carrera='wrc_2026_finlandia' LIMIT 10;"
```
