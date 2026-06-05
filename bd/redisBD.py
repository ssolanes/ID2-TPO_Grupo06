# Esto es para probar redis
import redis
import time
import random

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
r.set("p1_vel","0")

print("Corriendo redis...")

while True:
    nroRandom = random.randint(90,100)
    r.set("p1_vel",nroRandom)
    time.sleep(0.5)