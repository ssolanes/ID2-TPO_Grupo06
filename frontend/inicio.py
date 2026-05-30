from nicegui import ui
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@ui.page('/')
def inicio():
    
    # Contador de velocidad para probar redis y la actualizacion de los datos en tiempo real
    ui.label('Contador de velocidad').style('font-size: 2rem')

    etiquetaVelocidad = ui.label()
    r.set("p1_vel", "0")

    def tick():
        velocidad = r.get("p1_vel")
        etiquetaVelocidad.set_text(f'Velocidad de piloto 1: {velocidad} km/h')

    ui.timer(1.0, tick)