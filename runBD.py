# Este archivo sirve para correr la base de datos de redis (y despues tambien tendremos que hacer que corra la de cassandra)
# IMPORTANTE: para correr al mismo tiempo que run.py, clickear en la flecha al lado del icono de run
# y apretar en "Run Python File in Dedicated Terminal"

import os
import subprocess
import sys

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    scripts = [
        os.path.join(base, "bd", "redisBD.py"),
        os.path.join(base, "bd", "cassandraBD.py"),
    ]

    procesos = []
    for script in scripts:
        if not os.path.exists(script):
            print(f"No se encontro {script}")
            continue
        procesos.append(subprocess.Popen([sys.executable, script], cwd=base))

    for proceso in procesos:
        proceso.wait()

if __name__ == "__main__":
    main()
