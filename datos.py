import json
import os


def cargar(nombre_archivo):

    if not os.path.exists(nombre_archivo):
        return []

    with open(nombre_archivo, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar(nombre_archivo, datos):

    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)