# Este archivo sirve para correr la base de datos de redis (y despues tambien tendremos que hacer que corra la de cassandra)
# IMPORTANTE: para correr al mismo tiempo que run.py, clickear en la flecha al lado del icono de run
# y apretar en "Run Python File in Dedicated Terminal"

import subprocess
import sys
import os

def main():
    redis_script = os.path.join("bds", "redisBD.py")
    if not os.path.exists(redis_script):
        print(f"No se encontro {redis_script}")
        return
    subprocess.run([sys.executable, redis_script])

if __name__ == "__main__":
    main()