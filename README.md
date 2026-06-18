# TPO Ingenieria de Datos 2 - World Rally Cup

Proyecto en Python con NiceGUI para administrar datos de World Rally Cup usando MongoDB, Neo4j, Redis y Cassandra.

## Estado actual

- `run.py` levanta el selector principal.
- Datos estaticos en `localhost:8081`: CRUD MongoDB + relaciones Neo4j.
- Tiempo real en `localhost:8082`: Redis + Cassandra.
- MongoDB guarda las entidades principales.
- Al crear o editar entidades desde MongoDB, se crea o actualiza automaticamente su nodo en Neo4j.
- Neo4j se usa para crear relaciones entre nodos, no para crear nodos manualmente.
- Redis mantiene el estado vivo de carrera.
- Cassandra persiste el historico generado desde Redis.

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

Los formularios del frontend estan simplificados para cargar solo la informacion necesaria. Las relaciones entre entidades no se cargan en estos formularios.

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

Relaciones disponibles desde el frontend:

- Piloto pertenece a equipo.
- Piloto conduce vehiculo.
- Piloto tiene copiloto.
- Piloto participa en campeonato.
- Copiloto pertenece a equipo.
- Copiloto asiste en vehiculo.
- Copiloto participa en campeonato.
- Equipo usa vehiculo.
- Equipo participa en rally.
- Patrocinador patrocina equipo.
- Jefe de ingenieria dirige equipo.
- Temporada tiene campeonato.
- Campeonato tiene rally.
- Noticia / reporte habla de rally.
- Resumen de carrera resume rally.

No se crean relaciones Neo4j para fallas mecanicas ni para la estructura interna de rally (`Leg`, `SpecialStage`, `Split`).

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

Para cargar datos base en MongoDB:

```bash
python bd/mongoBD.py
```

Para cargar datos base en Neo4j:

```bash
python bd/neo4jBD.py
```

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
- `bd/mongoBD.py`: carga inicial de MongoDB.
- `bd/neo4jBD.py`: carga inicial de Neo4j.
- `bd/redisBD.py`: genera datos vivos de carrera en Redis.
- `bd/cassandraBD.py`: crea tablas y persiste historico en Cassandra.

## Notas

- Los botones de creacion de nodos Neo4j fueron removidos del frontend.
- Los nodos Neo4j se crean desde los CRUD MongoDB.
- Las relaciones se crean desde la pantalla `Neo4j - Relaciones`.
- Las noticias y resumenes se vinculan a rallies desde Neo4j, no mediante `rally_id` en MongoDB.
- Las fallas mecanicas quedan como dato del vehiculo en MongoDB, no como relacion Neo4j.
