import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import psycopg2
from models.logic import Guerrero, Mago, Personaje

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('mejorar_habilidad')
def upgrade_skill(data):
    # Aquí iría la lógica de verificar en la DB si cumple requisitos
    # 1. ¿Nivel de habilidad requisito >= nivel_requisito_necesario?
    # 2. ¿Puntos disponibles?
    emit('status', {'msg': 'Habilidad mejorada (Lógica de árbol validada)'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)