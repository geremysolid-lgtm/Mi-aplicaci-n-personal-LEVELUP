from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    xp_total = db.Column(db.Integer, default=0)
    racha = db.Column(db.Integer, default=0)
    creado = db.Column(db.DateTime, default=datetime.utcnow)


class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    nombre = db.Column(db.String(200), nullable=False)
    completada = db.Column(db.Boolean, default=False)
    creada = db.Column(db.DateTime, default=datetime.utcnow)


class Nota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    materia = db.Column(db.String(100))
    nota = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


class Meta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    nombre = db.Column(db.String(200))
    progreso = db.Column(db.Integer, default=0)


class SesionGym(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    ejercicio = db.Column(db.String(100))
    completado = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


class PuntosXP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    cantidad = db.Column(db.Integer, default=0)
    motivo = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

if __name__ == "__main__":
    from flask import Flask

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///levelup.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    print("Base de datos LEVELUP creada correctamente.")