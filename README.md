# TPO Ingenieria de Datos 2 - World Rally Cup

Estado actual:

- Frontend de inicio hecho

- Archivo para crear bd y cargar datos de Neo4J hecho, falta de MongoDB

- Frontend, conexion con db y crud para MongoDB hecho parcialmente, faltan agregar colecciones en el front

- Falta front de Neo4J, Redis y Cassandra

- Faltan archivos que creen bd y generen datos de Redis y Cassandra

#

Separamos las 4 bases de datos en 2 categorias

### Bases de datos estaticas: MongoDB y Neo4J

Estas se usan para datos que no cambian en tiempo real, sino que el usuario modifica estos datos mediante un crud

### Bases de datos no estaticas: Redis y Cassandra

Estas se usan para datos que cambian en tiempo real

En el frontend separamos estos 2 tipos de bases de datos en puertos distintos, para que asi haya mas aislamiento de dependencias y escalabilidad independiente 

#

Para instalar todas las librerias de python necesarias, correr 
    
    pip install -r requirements.txt

Esto basicamente te instala todo de una sin tener que ir haciendo pip install etc etc por cada cosa

Para correr la web, ejecutar run.py

Luego, se deberia ejecutar runBD.py para que se muestren los datos recibidos de redis y cassandra en tiempo real

    IMPORTANTE: para correr runBD.py al mismo tiempo que run.py , clickear en la flecha al lado del icono de run y apretar en "Run Python File in Dedicated Terminal"

runDB.py levanta el archivo redisBD.py (luego hay que implementar un cassandraBD.py para que tambien lo ejecute)


