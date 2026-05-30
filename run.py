# Este archivo sirve para correr la web pero sin que esten las bd de redis y cassandra mostrando datos en tiempo real 
from nicegui import ui
from frontend import inicio , piloto 

ui.run(dark=True)