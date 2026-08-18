from flask import Flask, render_template, request, redirect
from datetime import date
from datos import cargar, guardar
from puntos import sumar_xp, obtener_nivel, obtener_xp, xp_para_siguiente_nivel

from groq import Groq
from dotenv import load_dotenv
import os

app = Flask(__name__)
@app.context_processor
def datos_nivel():

    xp = obtener_xp()
    nivel = obtener_nivel()

    if nivel["nivel"] < 5:
        xp_inicio = nivel["xp_min"]
        xp_fin = nivel["xp_max"] + 1

        progreso = xp - xp_inicio
        necesario = xp_fin - xp_inicio

        porcentaje = int((progreso / necesario) * 100)

    else:
        porcentaje = 100

    return {
        "xp": xp,
        "nivel": nivel,
        "porcentaje_nivel": porcentaje
    }

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

lista_tareas = cargar("tareas.json")
lista_notas = cargar("notas.json")

# =====================================
# ENTRENAMIENTO
# =====================================

RUTINA_LMV = {
    "nombre": "Fuerza - Tren Superior",
    "dias": "Lunes, Miércoles y Viernes",
    "duracion": "40 minutos",
    "ejercicios": [
        {
            "nombre": "Dominadas",
            "series": 3,
            "reps": "7 repeticiones"
        },
        {
            "nombre": "Fondos (Dips)",
            "series": 3,
            "reps": "5 repeticiones"
        },
        {
            "nombre": "Flexiones de pecho",
            "series": 3,
            "reps": "15-20 repeticiones"
        },
        {
            "nombre": "Remo australiano en barra baja",
            "series": 3,
            "reps": "10-12 repeticiones"
        },
        {
            "nombre": "Elevación de rodillas en barra",
            "series": 3,
            "reps": "12-15 repeticiones"
        },
        {
            "nombre": "Plancha frontal",
            "series": 3,
            "reps": "45-60 segundos"
        },
        {
            "nombre": "Saltos de soga",
            "series": "5",
            "reps": "200-300 saltos"
        }
    ]
}
RUTINA_MJSD = {
    "nombre": "Fuerza - Tren Inferior",
    "dias": "Martes y Jueves",
    "duracion": "40 minutos",
    "ejercicios": [
        {
            "nombre": "Sentadillas libres",
            "series": 4,
            "reps": "20 repeticiones"
        },
        {
            "nombre": "Zancadas (Piernas)",
            "series": 3,
            "reps": "12 por pierna"
        },
        {
            "nombre": "Saltos de soga",
            "series": "5",
            "reps": "200-300 saltos"
        },
        {
            "nombre": "Elevación de rodillas en barra",
            "series": 3,
            "reps": "12-15 repeticiones"
        },
        {
            "nombre": "Plancha lateral",
            "series": 3,
            "reps": "30-45 segundos por lado"
        },
        {
            "nombre": "Mountain Climbers",
            "series": 3,
            "reps": "30-40 segundos"
        },
        {
            "nombre": "Crunch abdominal",
            "series": 3,
            "reps": "20 repeticiones"
        }
    ]
}

DESCANSO = {
    "nombre": "Descanso Activo",
    "dias": "Domingo",
    "duracion": "20 minutos",
    "ejercicios": [
        {
            "nombre": "Estiramientos",
            "series": 1,
            "reps": "10 minutos"
        }
    ]
}

def rutina_del_dia():

    dia = date.today().weekday()

    if dia in [0, 2, 4]:
        return RUTINA_LMV


    elif dia in [1, 3]:
        return RUTINA_MJSD

    else:
        return DESCANSO
def obtener_progreso_semana():

    semana = str(date.today().isocalendar()[1])

    progreso = cargar(f"progreso_semana_{semana}.json")

    if isinstance(progreso, dict):
        return progreso

    return {}

def guardar_progreso_semana(progreso):

    semana = str(date.today().isocalendar()[1])

    guardar(f"progreso_semana_{semana}.json", progreso)

@app.route("/")
def inicio():
    return render_template("index.html")
@app.route("/rutina", methods=["GET", "POST"])
def rutina():

    archivo = "rutina_diaria.json"

    progreso = cargar(archivo)

    if not isinstance(progreso, dict):
        progreso = {}

    hoy = str(date.today())

    if hoy not in progreso:
        progreso[hoy] = {}

    if request.method == "POST":

        actividad = request.form.get("actividad")

        if actividad and not progreso[hoy].get(actividad):

            progreso[hoy][actividad] = True

            guardar(archivo, progreso)

            sumar_xp("rutina")

    return render_template(
        "rutina.html",
        progreso=progreso[hoy]
    )
# =====================================
# ENTRENAMIENTO
# =====================================


@app.route("/entrenamiento")
def entrenamiento():

    rutina = rutina_del_dia()

    progreso = obtener_progreso_semana()

    hoy = str(date.today())

    progreso_hoy = progreso.get(hoy, {})

    return render_template(
        "entrenamiento.html",
        rutina=rutina,
        progreso=progreso_hoy
    )




@app.route("/entrenamiento/completar", methods=["POST"])
def completar_serie():

    ejercicio = request.form.get("ejercicio")

    hoy = str(date.today())

    progreso = obtener_progreso_semana()

    if hoy not in progreso:
        progreso[hoy] = {}

    actual = progreso[hoy].get(ejercicio, 0)

    progreso[hoy][ejercicio] = actual + 1

    guardar_progreso_semana(progreso)

    # SUMAR 10 XP POR COMPLETAR UNA SERIE
    sumar_xp("gym")

    return redirect("/entrenamiento")

# =====================================
# COMPLETAR TAREA
# =====================================

@app.route("/tareas/completar", methods=["POST"])
def completar_tarea():

    global lista_tareas

    tarea_buscada = request.form.get("tarea")

    if tarea_buscada:

        for i, tarea in enumerate(lista_tareas):

            # Si la tarea ya tiene formato de diccionario
            if isinstance(tarea, dict):

                texto = tarea.get("texto", "")

                if texto == tarea_buscada:

                    # Evitar ganar XP otra vez
                    if tarea.get("completada", False):
                        break

                    lista_tareas[i]["completada"] = True

                    guardar("tareas.json", lista_tareas)

                    # +10 XP
                    sumar_xp("tarea")

                    break

            # Si la tarea todavía es texto normal
            else:

                if tarea == tarea_buscada:

                    lista_tareas[i] = {
                        "texto": tarea,
                        "completada": True
                    }

                    guardar("tareas.json", lista_tareas)

                    # +10 XP
                    sumar_xp("tarea")

                    break

    return redirect("/tareas")


# =====================================
# TAREAS
# =====================================

@app.route("/tareas", methods=["GET", "POST"])
def pagina_tareas():

    global lista_tareas

    # AGREGAR TAREA
    if request.method == "POST":

        nueva_tarea = request.form.get("tarea")

        if nueva_tarea:

            lista_tareas.append(nueva_tarea)

            guardar(
                "tareas.json",
                lista_tareas
            )


    # BUSCADOR
    buscar = request.args.get(
        "buscar",
        ""
    ).lower()


    # FILTRAR TAREAS
    if buscar:

        tareas_filtradas = []

        for tarea in lista_tareas:

            if isinstance(tarea, dict):

                texto = tarea.get(
                    "texto",
                    ""
                )

            else:

                texto = tarea


            if buscar in texto.lower():

                tareas_filtradas.append(
                    tarea
                )

    else:

        tareas_filtradas = lista_tareas


    return render_template(
        "tareas.html",
        tareas=tareas_filtradas,
        buscar=buscar
    )


# =====================================
# ELIMINAR TAREA
# =====================================

@app.route("/eliminar/<int:id>")
def eliminar(id):

    global lista_tareas

    if 0 <= id < len(lista_tareas):

        lista_tareas.pop(id)

        guardar(
            "tareas.json",
            lista_tareas
        )

    return redirect("/tareas")


# =====================================
# NOTAS
# =====================================

@app.route("/notas", methods=["GET", "POST"])
def notas():

    global lista_notas

    if request.method == "POST":

        materia = request.form.get("materia")
        nota = request.form.get("nota")

        if materia and nota:

            lista_notas.append({
                "materia": materia,
                "nota": float(nota)
            })

            guardar("notas.json", lista_notas)

            # +5 XP por registrar una nota
            sumar_xp("nota")


    suma = 0

    for elemento in lista_notas:

        try:

            suma += float(elemento["nota"])

        except:

            pass


    if len(lista_notas) > 0:

        promedio = round(
            suma / len(lista_notas),
            2
        )

    else:

        promedio = 0


    return render_template(
        "notas.html",
        notas=lista_notas,
        promedio=promedio
    )


@app.route("/eliminar_nota/<int:id>")
def eliminar_nota(id):

    global lista_notas

    if 0 <= id < len(lista_notas):

        lista_notas.pop(id)

        guardar(
            "notas.json",
            lista_notas
        )

    return redirect("/notas")

# =====================================
# ESTADÍSTICAS
# =====================================

@app.route("/estadisticas")
def estadisticas():

    total_tareas = len(lista_tareas)

    total_notas = len(lista_notas)

    suma = 0

    for elemento in lista_notas:

        try:
            suma += float(elemento["nota"])
        except:
            pass

    if total_notas > 0:
        promedio = round(suma / total_notas, 2)
    else:
        promedio = 0

    return render_template(
        "estadisticas.html",
        total_tareas=total_tareas,
        total_notas=total_notas,
        promedio=promedio
    )


# =====================================
# ASISTENTE IA
# =====================================

@app.route("/asistente", methods=["GET", "POST"])
def asistente():

    respuesta = ""
    pregunta = ""

    if request.method == "POST":

        pregunta = request.form.get("pregunta", "").strip()

        if pregunta:

            try:

                completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[  
                        {
                            "role": "system",
                            "content": (
                                "Eres un asistente de estudio para Geremy, "
                                "un estudiante de 14 años. "
                                "Responde siempre en español, de forma clara, "
                                "con ejemplos sencillos. "
                                "Si la pregunta es de programación, utiliza Python "
                                "cuando sea posible."
                            )
                        },
                        {
                            "role": "user",
                            "content": pregunta
                        }
                    ],
                    temperature=0.7,
                    max_tokens=500
                )

                respuesta = completion.choices[0].message.content

            except Exception as e:

                respuesta = f"Error al conectar con Groq: {e}"

    return render_template(
        "asistente.html",
        respuesta=respuesta,
        pregunta=pregunta
    )

if __name__ == "__main__":
    app.run(debug=True)