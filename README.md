# TPO Ingenieria de Datos 2 - World Rally Cup

Proyecto en Python con NiceGUI para visualizar datos de World Rally Cup usando bases de datos estaticas y bases de datos de tiempo real.

## Estado actual

- Frontend selector principal en `run.py`.
- Frontend estatico en `localhost:8081` para MongoDB y Neo4j.
- Frontend de tiempo real en `localhost:8082` para Redis y Cassandra.
- Redis genera y mantiene el estado instantaneo de la carrera.
- Cassandra persiste el historico a partir de los eventos generados por Redis.
- MongoDB y Neo4j quedan como modulo estatico

## Cosas que faltan

- Archivo de dataset de MongoDB
- Terminar frontend MongoDB (faltan colecciones y pulir apartado visual)
- Frontend de Neo4J
- Unificar crud de MongoDB y Neo4J
- Pulir apartado visual de modulo de tiempo real

## Separacion de bases de datos

### Bases de datos estaticas: MongoDB y Neo4j

Se usan para datos que no cambian constantemente, como pilotos, equipos, rallies, patrocinadores y relaciones. El usuario modifica estos datos mediante pantallas tipo CRUD.

### Bases de datos no estaticas: Redis y Cassandra

Se usan para datos que cambian durante la carrera.

Redis guarda el estado vivo:

- Auto actualmente en tramo.
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

Cassandra guarda el historico:

- Telemetria historica.
- Tiempos por checkpoint.
- Ranking temporal guardado.
- Eventos de carrera.

## Logica de rally implementada

En rally no corren todos los autos al mismo tiempo. Por eso el modulo de tiempo real simula un solo auto activo por vez.

El flujo es:

1. Redis carga tiempos de referencia para cada piloto.
2. Un piloto entra al tramo `SS1`.
3. El piloto avanza checkpoint por checkpoint.
4. Mientras esta en tramo, Redis actualiza telemetria y tiempo parcial.
5. Cuando llega al ultimo checkpoint, se actualiza su tiempo final en el ranking.
6. Luego se habilita el siguiente piloto.
7. Cassandra lee los eventos del stream de Redis y los guarda como historico.

Los tiempos se muestran en formato `hh:mm:ss.mmm`.

## Instalacion

Para instalar todas las librerias de Python necesarias:

```bash
pip install -r requirements.txt
```

## Ejecucion

Primero levantar los procesos de Redis y Cassandra: (SE ESTA TESTEANDO SALTEAR ESTE PASO, TODAVIA NO ESTA CONFIRMADO)

```bash
python runBD.py
```

Luego, en otra terminal, levantar la web:

```bash
python run.py
```

El selector principal queda en:

```text
http://localhost:8080
```

Los modulos quedan separados en:

```text
http://localhost:8081  Datos estaticos: MongoDB + Neo4j
http://localhost:8082  Tiempo real: Redis + Cassandra
```

## Requisitos de servicios locales

Se debe haber creado una instancia de Neo4J con los siguientes datos:

```text
USER = "neo4j" 
PASSWORD = "12345678"
```

Redis debe estar disponible en:

```text
localhost:6379
```

Cassandra se usa desde el contenedor Docker:

```text
cassandra-demo
```

El script `bd/cassandraBD.py` usa `docker exec cassandra-demo cqlsh` para crear tablas y persistir datos, porque el driver Python de Cassandra no funciona correctamente con Python 3.14 en este entorno.


## Archivos principales

- `run.py`: levanta el selector y los dos frontends.
- `runBD.py`: levanta los procesos de Redis y Cassandra.
- `bd/redisBD.py`: genera datos vivos de carrera en Redis.
- `bd/cassandraBD.py`: crea tablas y persiste historico en Cassandra
- `bd/neo4jBD.py`: crea bd e inserta datos en neo4j
- `run_frontends/run_realtime.py`: muestra el panel de tiempo real.
- `run_frontends/run_static.py`: muestra el panel estatico.

