# TPO Ingenieria de Datos 2 - World Rally Cup

Proyecto en Python con NiceGUI para administrar datos de World Rally Cup usando MongoDB, Neo4j, Redis y Cassandra.

## Modelo de datos

### MongoDB

MongoDB guarda los datos propios de cada entidad:

- Pilotos.
- Copilotos.
- Equipos.
- Vehiculos.
- Patrocinadores.
- Jefes de ingenieria.
- Rallies.
- Resumenes de carrera.
- Noticias y reportes.

Los formularios del frontend estan simplificados para cargar solo los campos de MongoDB. Las relaciones entre entidades se ven apretando el icono de conexion.


### Rally en MongoDB

La estructura interna del rally queda guardada dentro del documento MongoDB:

- Legs.
- Special stages.
- Splits.

Al crear un rally se puede elegir:

- Cantidad de dias / legs.
- Special stages por dia.
- Splits por special stage.

Esa estructura no se modela como relaciones Neo4j.

### Neo4j

Neo4j guarda relaciones entre entidades grandes del dominio. Los nodos se crean automaticamente desde MongoDB.
Cada nodo Neo4j conserva solo datos minimos de visualizacion: `mongo_id`, `nombre` y, cuando hace falta por compatibilidad del frontend, un alias como `modelo`, `titular` o `titulo`. Los datos descriptivos completos viven en MongoDB.

Relaciones disponibles desde el frontend:

- Campeonato -(Tiene_Rally)-> Rally
- Piloto -(Pertenece a)-> Equipo
- Copiloto -(Pertenece a)-> Equipo
- Jefe de Ingeniería -(Dirige)-> Equipo
- Equipo -(Usa)-> Vehículo
- Equipo -(Participa en)-> Rally
- Piloto -(Conduce)-> Vehículo
- Copiloto -(Asiste en)-> Vehículo
- Piloto -(Participa en)-> Campeonato
- Copiloto -(Participa en)-> Campeonato
- Patrocinador -(Patrocina a)-> Equipo
- Noticia / Reporte -(Habla de)-> Rally
- Resumen de Carrera -(Resume)-> Rally



## Bases de datos de tiempo real

### Redis

Redis guarda el estado vivo de la carrera:

- Auto actualmente en special stage.
- Piloto activo y siguiente piloto.
- Ranking en vivo.
- Tiempos de referencia a superar.
- Checkpoint actual.
- Posicion GPS actual.
- Velocidad actual.
- RPM actual.
- Temperatura actual.
- Sesiones activas de usuarios.
- Stream de eventos de carrera.

### Cassandra

Cassandra guarda el historico:

- Telemetria historica.
- Tiempos por checkpoint.
- Ranking temporal guardado.
- Eventos de carrera.

## Logica de carrera

En rally no corren todos los autos al mismo tiempo. Por eso el modulo de tiempo real simula un solo auto activo por vez.

Flujo:

1. Redis carga tiempos de referencia para cada piloto.
2. Un piloto entra a una special stage.
3. El piloto avanza checkpoint por checkpoint.
4. Redis actualiza telemetria y tiempo parcial.
5. Al llegar al ultimo checkpoint, se actualiza su tiempo final en el ranking.
6. Se habilita el siguiente piloto.
7. Cassandra lee los eventos del stream de Redis y los guarda como historico.

Los tiempos se muestran en formato `hh:mm:ss.mmm`.

## Instalacion

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Servicios requeridos

Antes de ejecutar la app, levantar los contenedores Docker:

- MongoDB en `localhost:27017`.
- Neo4j Bolt en `localhost:7687`.
- Neo4j Browser en `localhost:7474`.
- Redis en `localhost:6379`.
- Cassandra en `localhost:9042`.

Neo4j debe estar configurado con:

```text
USER = "neo4j"
PASSWORD = "12345678"
```

Si tu password de Neo4j es distinto, cambiarlo en `frontend_static/shared.py` y en los scripts que correspondan.

## Carga inicial de datos

Para cargar datos base en MongoDB y Neo4j, correr:

```bash
python bd/dataset_MongoNeo.py
```

El script genera todos los datos en memoria utilizando diccionarios de Python (con claves temporales para las relaciones), los inserta primero en MongoDB, que les asigna los _id reales, y luego usa esos mismos objetos en memoria (ya con _id de Mongo) para crear en Neo4j nodos livianos (mongo_id + nombre) y las relaciones entre ellos, resolviendo las claves temporales a _id reales en el proceso; antes de empezar borra todo lo existente en ambas bases para poder correrse varias veces sin duplicar, y al final valida que la cantidad de documentos y nodos/relaciones insertados coincida con lo esperado.

Despues, al usar el frontend estatico, los nuevos documentos MongoDB crean automaticamente su nodo Neo4j.

## Ejecucion

Levantar la app:

```bash
python run.py
```

Selector principal:

```text
http://localhost:8080
```

Modulos:

```text
http://localhost:8081  Datos estaticos: MongoDB + Neo4j
http://localhost:8082  Tiempo real: Redis + Cassandra
```

## Archivos principales

- `run.py`: levanta el selector principal.
- `run_frontends/run_static.py`: frontend de MongoDB + Neo4j.
- `run_frontends/run_realtime.py`: frontend de Redis + Cassandra.
- `frontend_static/shared.py`: conexiones compartidas y sincronizacion MongoDB -> Neo4j.
- `frontend_static/pages/neo4j_relaciones.py`: pantalla para crear relaciones Neo4j.
- `bd/dataset_MongoNeo.py`: carga inicial de MongoDBy Neo4j
- `bd/redisBD.py`: genera datos vivos de carrera en Redis.
- `bd/cassandraBD.py`: crea tablas y persiste historico en Cassandra.
