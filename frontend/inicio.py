import subprocess
from nicegui import ui
import redis

# Arrancar el contenedor redis si no está corriendo
subprocess.run(["docker", "start", "redis"], capture_output=True)

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@ui.page('/')
def inicio():
    ui.label('Contador de velocidad').style('font-size: 2rem')

    etiquetaVelocidad = ui.label()
    r.set("p1_vel", "0")

    def tick():
        velocidad = r.get("p1_vel")
        etiquetaVelocidad.set_text(f'Velocidad de piloto 1: {velocidad} km/h')

    ui.timer(1.0, tick)