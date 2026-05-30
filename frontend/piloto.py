# Esto lo hice solo para probar mongo y probar hacer subpaginas
# no les deberia funcionar porque no tienen los mismos datos de mongo
# esto luego deberia funcionar como un crud
from nicegui import ui
from pymongo import MongoClient
from bson import ObjectId

cliente = MongoClient("mongodb://localhost:27017/")

db = cliente["wrcPrueba"]
coleccion = db["pilotos"]

@ui.page('/piloto')
def inicio():
    ui.label('Piloto 1').style('font-size: 2rem')
    doc = coleccion.find_one({"_id": ObjectId("6a1a87da5eb6eacecb5e6261")})
    ui.label(f"Nombre: {doc['nombre']}")
    ui.label(f"Auto: {doc['auto']}")
    ui.label(f"Sponsor: {doc['sponsor']}")
    
    