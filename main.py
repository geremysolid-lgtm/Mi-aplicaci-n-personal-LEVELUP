from flask import Flask, render_template, request, redirect
from datetime import date, datetime
from dotenv import load_dotenv
from groq import Groq

from datos import cargar, guardar
from puntos import sumar_xp, obtener_nivel, obtener_xp, xp_para_siguiente_nivel

from database import (
    db,
    Usuario,
    Tarea,
    Nota,
    Meta,
    SesionGym,
    PuntosXP
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import os


# =====================================
# CONFIGURACIÓN
# =====================================

app = Flask(__name__)

app.secret_key = "clave-secreta-levelup"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///levelup.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# =====================================
# LOGIN
# =====================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def cargar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


# =====================================
# NIVEL / XP
# =====================================

@app.context_processor
def datos_nivel():

    xp = obtener_xp()
    nivel = obtener_nivel()

    if nivel["nivel"] < 5:

        xp_inicio = nivel["xp_min"]
        xp_fin = nivel["xp_max"] + 1

        progreso = xp - xp_inicio
        necesario = xp_fin - xp_inicio

        if necesario > 0:
            porcentaje = int((progreso / necesario) * 100)
        else:
            porcentaje = 0

    else:
        porcentaje = 100

    return {
        "xp": xp,
        "nivel": nivel,
        "porcentaje_nivel": porcentaje
    }


# =====================================
# GROQ
# =====================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# =====================================
# DATOS ANTIGUOS
# =====================================

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


# =====================================
# PROGRESO SEMANAL DE ENTRENAMIENTO
# =====================================

def obtener_progreso_semana():

    semana = str(date.today().isocalendar()[1])

    progreso = cargar(
        f"progreso_semana_{semana}.json"
    )

    if isinstance(progreso, dict):
        return progreso

    return {}


def guardar_progreso_semana(progreso):

    semana = str(date.today().isocalendar()[1])

    guardar(
        f"progreso_semana_{semana}.json",
        progreso
    )


# =====================================
# RUTINAS FAMILIARES
# =====================================

def archivo_rutina_familiar(usuario_id):

    return f"rutina_familiar_{usuario_id}.json"


def obtener_rutina_familiar(usuario_id):

    rutina = cargar(
        archivo_rutina_familiar(usuario_id)
    )

    if isinstance(rutina, dict):
        return rutina

    return {
        "manana": {
            "activa": True,
            "actividades": []
        },
        "tarde": {
            "activa": True,
            "actividades": []
        },
        "noche": {
            "activa": True,
            "actividades": []
        },
        "bootcamp": {
            "activa": True,
            "actividades": []
        }
    }


def guardar_rutina_familiar(usuario_id, rutina):

    guardar(
        archivo_rutina_familiar(usuario_id),
        rutina
    )


# =====================================
# INICIO
# =====================================

@app.route("/")
def inicio():

    if current_user.is_authenticated:

        if current_user.rol == "padre":
            return redirect("/panel-padre")

        return redirect("/panel-hijo")

    return render_template("index.html")


# =====================================
# RUTINA
# =====================================

@app.route("/rutina", methods=["GET", "POST"])
@login_required
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

            guardar(
                archivo,
                progreso
            )

            sumar_xp("rutina")

    return render_template(
        "rutina.html",
        progreso=progreso[hoy]
    )


# =====================================
# ENTRENAMIENTO
# =====================================

@app.route("/entrenamiento")
@login_required
def entrenamiento():

    rutina = rutina_del_dia()

    progreso = obtener_progreso_semana()

    hoy = str(date.today())

    progreso_hoy = progreso.get(
        hoy,
        {}
    )

    return render_template(
        "entrenamiento.html",
        rutina=rutina,
        progreso=progreso_hoy
    )


@app.route("/entrenamiento/completar", methods=["POST"])
@login_required
def completar_serie():

    ejercicio = request.form.get("ejercicio")

    if not ejercicio:
        return redirect("/entrenamiento")

    hoy = str(date.today())

    progreso = obtener_progreso_semana()

    if hoy not in progreso:
        progreso[hoy] = {}

    actual = progreso[hoy].get(
        ejercicio,
        0
    )

    progreso[hoy][ejercicio] = actual + 1

    guardar_progreso_semana(progreso)

    # Registrar también en SQLite
    nueva_sesion = SesionGym(
        usuario_id=current_user.id,
        ejercicio=ejercicio,
        completado=True
    )

    db.session.add(nueva_sesion)
    db.session.commit()

    # +10 XP
    sumar_xp("gym")

    return redirect("/entrenamiento")


# =====================================
# COMPLETAR TAREA
# =====================================

@app.route("/tareas/completar", methods=["POST"])
@login_required
def completar_tarea():

    tarea_id = request.form.get("id")

    if tarea_id:

        tarea = Tarea.query.filter_by(
            id=int(tarea_id),
            usuario_id=current_user.id
        ).first()

        if tarea and not tarea.completada:

            tarea.completada = True

            db.session.commit()

            sumar_xp("tarea")

    return redirect("/tareas")


# =====================================
# REGISTRO
# =====================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        email = request.form.get(
            "email"
        )

        password = request.form.get(
            "password"
        )

        rol = request.form.get(
            "rol"
        )

        codigo_padre = request.form.get(
            "codigo_padre"
        )

        # ---------------------------------
        # VALIDACIONES
        # ---------------------------------

        if not username or not email or not password:
            return "Todos los campos son obligatorios."

        if rol not in ["padre", "hijo"]:
            return "Tipo de cuenta incorrecto."

        # ---------------------------------
        # COMPROBAR USUARIO EXISTENTE
        # ---------------------------------

        usuario_existente = Usuario.query.filter(
            (Usuario.username == username) |
            (Usuario.email == email)
        ).first()

        if usuario_existente:
            return "El usuario o correo ya existe."

        # ---------------------------------
        # CREAR USUARIO
        # ---------------------------------

        nuevo_usuario = Usuario(
            username=username,
            email=email,
            password=generate_password_hash(password),
            rol=rol
        )

        # ---------------------------------
        # PADRE
        # ---------------------------------

        if rol == "padre":

            nuevo_usuario.generar_codigo()

        # ---------------------------------
        # HIJO
        # ---------------------------------

        elif rol == "hijo":

            if not codigo_padre:
                return "El hijo necesita el código del padre."

            padre = Usuario.query.filter_by(
                codigo=codigo_padre,
                rol="padre"
            ).first()

            if not padre:
                return "Código del padre incorrecto."

            nuevo_usuario.padre_id = padre.id

        # ---------------------------------
        # GUARDAR
        # ---------------------------------

        db.session.add(nuevo_usuario)

        db.session.commit()

        # ---------------------------------
        # RESPUESTA PADRE
        # ---------------------------------

        if rol == "padre":

            return (
                "Cuenta creada correctamente.<br><br>"
                "Tu código de familia es: "
                f"<strong>{nuevo_usuario.codigo}</strong><br><br>"
                '<a href="/login">Ir al login</a>'
            )

        return redirect("/login")

    return render_template(
        "registro.html"
    )


# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        usuario = Usuario.query.filter_by(
            username=username
        ).first()

        if usuario and check_password_hash(
            usuario.password,
            password
        ):

            login_user(usuario)

            if usuario.rol == "padre":
                return redirect("/panel-padre")

            return redirect("/panel-hijo")

        return "Usuario o contraseña incorrectos."

    return render_template(
        "login.html"
    )


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")


# =====================================
# TAREAS
# =====================================

@app.route("/tareas", methods=["GET", "POST"])
@login_required
def pagina_tareas():

    # ---------------------------------
    # AGREGAR TAREA
    # ---------------------------------

    if request.method == "POST":

        nueva_tarea = request.form.get(
            "tarea"
        )

        if nueva_tarea:

            tarea = Tarea(
                nombre=nueva_tarea,
                completada=False,
                usuario_id=current_user.id
            )

            db.session.add(tarea)

            db.session.commit()

    # ---------------------------------
    # BUSCADOR
    # ---------------------------------

    buscar = request.args.get(
        "buscar",
        ""
    ).lower()

    # ---------------------------------
    # TAREAS DEL USUARIO
    # ---------------------------------

    tareas = Tarea.query.filter_by(
        usuario_id=current_user.id
    ).order_by(
        Tarea.id.desc()
    ).all()

    # ---------------------------------
    # FILTRAR
    # ---------------------------------

    if buscar:

        tareas_filtradas = [
            tarea
            for tarea in tareas
            if buscar in tarea.nombre.lower()
        ]

    else:

        tareas_filtradas = tareas

    return render_template(
        "tareas.html",
        tareas=tareas_filtradas,
        buscar=buscar
    )


# =====================================
# ELIMINAR TAREA
# =====================================

@app.route("/eliminar/<int:id>")
@login_required
def eliminar(id):

    tarea = Tarea.query.filter_by(
        id=id,
        usuario_id=current_user.id
    ).first()

    if tarea:

        db.session.delete(tarea)

        db.session.commit()

    return redirect("/tareas")


# =====================================
# NOTAS
# =====================================

@app.route("/notas", methods=["GET", "POST"])
@login_required
def notas():

    # ---------------------------------
    # AGREGAR NOTA
    # ---------------------------------

    if request.method == "POST":

        materia = request.form.get(
            "materia"
        )

        nota_valor = request.form.get(
            "nota"
        )

        if materia and nota_valor:

            nueva_nota = Nota(
                materia=materia,
                nota=float(nota_valor),
                usuario_id=current_user.id
            )

            db.session.add(nueva_nota)

            db.session.commit()

            sumar_xp("nota")

    # ---------------------------------
    # OBTENER NOTAS
    # ---------------------------------

    lista_notas_db = Nota.query.filter_by(
        usuario_id=current_user.id
    ).order_by(
        Nota.id.desc()
    ).all()

    # ---------------------------------
    # PROMEDIO
    # ---------------------------------

    suma = 0

    for elemento in lista_notas_db:

        suma += float(
            elemento.nota
        )

    if len(lista_notas_db) > 0:

        promedio = round(
            suma / len(lista_notas_db),
            2
        )

    else:

        promedio = 0

    return render_template(
        "notas.html",
        notas=lista_notas_db,
        promedio=promedio
    )


# =====================================
# ELIMINAR NOTA
# =====================================

@app.route("/eliminar_nota/<int:id>")
@login_required
def eliminar_nota(id):

    nota = Nota.query.filter_by(
        id=id,
        usuario_id=current_user.id
    ).first()

    if nota:

        db.session.delete(nota)

        db.session.commit()

    return redirect("/notas")


# =====================================
# ESTADÍSTICAS
# =====================================

@app.route("/estadisticas")
@login_required
def estadisticas():

    total_tareas = Tarea.query.filter_by(
        usuario_id=current_user.id
    ).count()

    total_notas = Nota.query.filter_by(
        usuario_id=current_user.id
    ).count()

    notas_db = Nota.query.filter_by(
        usuario_id=current_user.id
    ).all()

    suma = 0

    for elemento in notas_db:

        suma += float(
            elemento.nota
        )

    if total_notas > 0:

        promedio = round(
            suma / total_notas,
            2
        )

    else:

        promedio = 0

    return render_template(
        "estadisticas.html",
        total_tareas=total_tareas,
        total_notas=total_notas,
        promedio=promedio
    )


# =====================================
# PANEL DEL PADRE
# =====================================

@app.route("/panel-padre")
@login_required
def panel_padre():

    # ---------------------------------
    # SOLO PADRES
    # ---------------------------------

    if current_user.rol != "padre":
        return redirect("/panel-hijo")

    # ---------------------------------
    # BUSCAR HIJOS
    # ---------------------------------

    hijos = Usuario.query.filter_by(
        padre_id=current_user.id
    ).all()

    # ---------------------------------
    # SI NO TIENE HIJOS
    # ---------------------------------

    if not hijos:

        return render_template(
            "panel_padre.html",
            hijos=[],
            hijo=None,
            tareas=[],
            notas=[],
            promedio=0,
            sesiones_gym=[],
            rutina_familiar=None,
            actividades_completadas=0
        )

    # ---------------------------------
    # HIJO SELECCIONADO
    # ---------------------------------

    hijo_id = request.args.get(
        "hijo_id",
        type=int
    )

    hijo = None

    if hijo_id:

        hijo = Usuario.query.filter_by(
            id=hijo_id,
            padre_id=current_user.id
        ).first()

    if not hijo:
        hijo = hijos[0]

    # ---------------------------------
    # TAREAS DEL HIJO
    # ---------------------------------

    tareas = Tarea.query.filter_by(
        usuario_id=hijo.id
    ).order_by(
        Tarea.id.desc()
    ).all()

    # ---------------------------------
    # TAREAS COMPLETADAS
    # ---------------------------------

    actividades_completadas = sum(
        1
        for tarea in tareas
        if tarea.completada
    )

    # ---------------------------------
    # NOTAS DEL HIJO
    # ---------------------------------

    notas = Nota.query.filter_by(
        usuario_id=hijo.id
    ).order_by(
        Nota.id.desc()
    ).all()

    suma_notas = 0

    for nota in notas:

        suma_notas += float(
            nota.nota
        )

    if notas:

        promedio = round(
            suma_notas / len(notas),
            2
        )

    else:

        promedio = 0

    # ---------------------------------
    # EJERCICIO DEL HIJO
    # ---------------------------------

    hoy_inicio = datetime.combine(
        date.today(),
        datetime.min.time()
    )

    manana = hoy_inicio.replace(
        day=hoy_inicio.day
    )

    sesiones_gym = SesionGym.query.filter(
        SesionGym.usuario_id == hijo.id,
        SesionGym.fecha >= hoy_inicio
    ).order_by(
        SesionGym.fecha.desc()
    ).all()

    # ---------------------------------
    # RUTINA FAMILIAR
    # ---------------------------------

    rutina_familiar = obtener_rutina_familiar(
        hijo.id
    )

    return render_template(
        "panel_padre.html",
        hijos=hijos,
        hijo=hijo,
        tareas=tareas,
        notas=notas,
        promedio=promedio,
        sesiones_gym=sesiones_gym,
        rutina_familiar=rutina_familiar,
        actividades_completadas=actividades_completadas
    )


# =====================================
# PANEL DEL HIJO
# =====================================

@app.route("/panel-hijo")
@login_required
def panel_hijo():

    # ---------------------------------
    # SOLO HIJOS
    # ---------------------------------

    if current_user.rol != "hijo":
        return redirect("/panel-padre")

    # ---------------------------------
    # TAREAS
    # ---------------------------------

    tareas = Tarea.query.filter_by(
        usuario_id=current_user.id
    ).order_by(
        Tarea.id.desc()
    ).all()

    tareas_completadas = [
        tarea
        for tarea in tareas
        if tarea.completada
    ]

    tareas_pendientes = [
        tarea
        for tarea in tareas
        if not tarea.completada
    ]

    # ---------------------------------
    # RUTINA FAMILIAR
    # ---------------------------------

    rutina_familiar = obtener_rutina_familiar(
        current_user.id
    )

    # ---------------------------------
    # NIVEL
    # ---------------------------------

    xp = current_user.xp_total or 0

    nivel = obtener_nivel()

    # ---------------------------------
    # LOGROS BÁSICOS
    # ---------------------------------
    #
    # No existe todavía un modelo Logro
    # en database.py.
    #
    # Por eso no inventamos una tabla.
    # Mostramos pequeños reconocimientos
    # basados en datos que ya existen.
    #

    logros = []

    if xp >= 100:
        logros.append(
            "🏆 Primeros 100 XP"
        )

    if len(tareas_completadas) >= 5:
        logros.append(
            "✅ 5 tareas completadas"
        )

    if current_user.racha >= 3:
        logros.append(
            "🔥 Racha de 3 días"
        )

    # ---------------------------------
    # MENSAJE IA
    # ---------------------------------

    mensaje = (
        f"¡Vamos {current_user.username}! "
        "Cada actividad que completas te acerca "
        "a tu siguiente nivel."
    )

    return render_template(
        "panel_hijo.html",
        hijo=current_user,
        tareas=tareas,
        tareas_completadas=tareas_completadas,
        tareas_pendientes=tareas_pendientes,
        rutina_familiar=rutina_familiar,
        xp=xp,
        nivel=nivel,
        logros=logros,
        mensaje=mensaje
    )


# =====================================
# CONFIGURACIÓN FAMILIAR
# =====================================

@app.route(
    "/configurar-rutina/<int:hijo_id>",
    methods=["GET", "POST"]
)
@login_required
def configurar_rutina(hijo_id):

    # ---------------------------------
    # SOLO PADRES
    # ---------------------------------

    if current_user.rol != "padre":
        return redirect("/panel-hijo")

    # ---------------------------------
    # COMPROBAR QUE EL HIJO PERTENECE
    # AL PADRE ACTUAL
    # ---------------------------------

    hijo = Usuario.query.filter_by(
        id=hijo_id,
        padre_id=current_user.id,
        rol="hijo"
    ).first()

    if not hijo:

        return "No tienes permiso para configurar este usuario."

    # ---------------------------------
    # CARGAR RUTINA
    # ---------------------------------

    rutina = obtener_rutina_familiar(
        hijo.id
    )

    # ---------------------------------
    # GUARDAR CAMBIOS
    # ---------------------------------

    if request.method == "POST":

        seccion = request.form.get(
            "seccion"
        )

        actividad = request.form.get(
            "actividad"
        )

        if seccion not in [
            "manana",
            "tarde",
            "noche",
            "bootcamp"
        ]:

            return "Sección incorrecta."

        if actividad:

            rutina[seccion][
                "actividades"
            ].append(
                actividad.strip()
            )

        guardar_rutina_familiar(
            hijo.id,
            rutina
        )

        return redirect(
            f"/configurar-rutina/{hijo.id}"
        )

    return render_template(
        "configurar_rutina.html",
        hijo=hijo,
        rutina=rutina
    )


# =====================================
# ACTIVAR / DESACTIVAR SECCIÓN
# =====================================

@app.route(
    "/configurar-rutina/<int:hijo_id>/seccion/<seccion>",
    methods=["POST"]
)
@login_required
def cambiar_seccion_rutina(
    hijo_id,
    seccion
):

    if current_user.rol != "padre":
        return redirect("/panel-hijo")

    hijo = Usuario.query.filter_by(
        id=hijo_id,
        padre_id=current_user.id,
        rol="hijo"
    ).first()

    if not hijo:
        return "No tienes permiso."

    if seccion not in [
        "manana",
        "tarde",
        "noche",
        "bootcamp"
    ]:
        return "Sección incorrecta."

    rutina = obtener_rutina_familiar(
        hijo.id
    )

    rutina[seccion]["activa"] = not rutina[
        seccion
    ]["activa"]

    guardar_rutina_familiar(
        hijo.id,
        rutina
    )

    return redirect(
        f"/configurar-rutina/{hijo.id}"
    )


# =====================================
# ELIMINAR ACTIVIDAD DE RUTINA
# =====================================

@app.route(
    "/configurar-rutina/<int:hijo_id>/eliminar",
    methods=["POST"]
)
@login_required
def eliminar_actividad_rutina(
    hijo_id
):

    if current_user.rol != "padre":
        return redirect("/panel-hijo")

    hijo = Usuario.query.filter_by(
        id=hijo_id,
        padre_id=current_user.id,
        rol="hijo"
    ).first()

    if not hijo:
        return "No tienes permiso."

    seccion = request.form.get(
        "seccion"
    )

    indice = request.form.get(
        "indice",
        type=int
    )

    if seccion not in [
        "manana",
        "tarde",
        "noche",
        "bootcamp"
    ]:
        return "Sección incorrecta."

    rutina = obtener_rutina_familiar(
        hijo.id
    )

    actividades = rutina[seccion][
        "actividades"
    ]

    if indice is not None:

        if 0 <= indice < len(actividades):

            actividades.pop(indice)

    guardar_rutina_familiar(
        hijo.id,
        rutina
    )

    return redirect(
        f"/configurar-rutina/{hijo.id}"
    )


# =====================================
# ASISTENTE IA
# =====================================

@app.route(
    "/asistente",
    methods=["GET", "POST"]
)
@login_required
def asistente():

    respuesta = ""

    pregunta = ""

    if request.method == "POST":

        pregunta = request.form.get(
            "pregunta",
            ""
        ).strip()

        if pregunta:

            try:

                completion = client.chat.completions.create(

                    model="openai/gpt-oss-120b",

                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Eres un asistente de estudio "
                                "para Geremy, un estudiante "
                                "de 14 años. "
                                "Responde siempre en español, "
                                "de forma clara, con ejemplos "
                                "sencillos. "
                                "Si la pregunta es de programación, "
                                "utiliza Python cuando sea posible."
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

                respuesta = (
                    completion
                    .choices[0]
                    .message
                    .content
                )

            except Exception as e:

                respuesta = (
                    f"Error al conectar con Groq: {e}"
                )

    return render_template(
        "asistente.html",
        respuesta=respuesta,
        pregunta=pregunta
    )


# =====================================
# CREAR TABLAS
# =====================================

with app.app_context():

    db.create_all()


# =====================================
# INICIAR APP
# =====================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )