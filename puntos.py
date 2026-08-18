import json
import os
from datetime import date


# =====================================
# NIVELES
# =====================================

NIVELES = [
    {
        "nivel": 1,
        "nombre": "ROOKIE",
        "xp_min": 0,
        "xp_max": 99
    },
    {
        "nivel": 2,
        "nombre": "TRAINEE",
        "xp_min": 100,
        "xp_max": 249
    },
    {
        "nivel": 3,
        "nombre": "WARRIOR",
        "xp_min": 250,
        "xp_max": 499
    },
    {
        "nivel": 4,
        "nombre": "CHAMPION",
        "xp_min": 500,
        "xp_max": 999
    },
    {
        "nivel": 5,
        "nombre": "ELITE",
        "xp_min": 1000,
        "xp_max": 99999
    }
]


# =====================================
# XP POR ACCIÓN
# =====================================

XP_POR_ACCION = {
    "rutina": 5,
    "tarea": 15,
    "gym": 10,
    "nota": 10,
    "meta": 20,
    "racha": 50,
    "dia_completo": 100
}


# =====================================
# CARGAR XP
# =====================================

def _cargar():

    if os.path.exists("data/xp.json"):

        with open("data/xp.json", "r", encoding="utf-8") as archivo:

            return json.load(archivo)

    return {
        "xp_total": 0,
        "historial": []
    }


# =====================================
# GUARDAR XP
# =====================================

def _guardar(datos):

    os.makedirs("data", exist_ok=True)

    with open(
        "data/xp.json",
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=4
        )


# =====================================
# SUMAR XP
# =====================================

def sumar_xp(accion):

    cantidad = XP_POR_ACCION.get(accion, 5)

    datos = _cargar()

    datos["xp_total"] += cantidad

    datos["historial"].append({
        "accion": accion,
        "xp": cantidad,
        "fecha": str(date.today())
    })

    _guardar(datos)

    return datos["xp_total"]


# =====================================
# OBTENER XP
# =====================================

def obtener_xp():

    return _cargar()["xp_total"]


# =====================================
# OBTENER NIVEL
# =====================================

def obtener_nivel():

    xp = obtener_xp()

    for nivel in reversed(NIVELES):

        if xp >= nivel["xp_min"]:

            return nivel

    return NIVELES[0]


# =====================================
# XP PARA SIGUIENTE NIVEL
# =====================================

def xp_para_siguiente_nivel():

    nivel = obtener_nivel()

    xp = obtener_xp()

    if nivel["nivel"] < 5:

        return nivel["xp_max"] - xp + 1

    return 0