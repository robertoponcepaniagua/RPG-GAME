import os
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit
import psycopg2
from contextlib import contextmanager

# En app.py
from models.Personaje import Personaje
from models.Enemigo import Enemigo
from models.Guerrero import Guerrero
from models.Mago import Mago
from models.Inventario import Inventario
from models.Item import Item
from models.Logro import Logro
from models.Personaje_Logro import Personaje_Logro


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- DEFINICIÓN DE LA URL ----
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rpguser:rpgpassword@db:5432/rpg_db")

# --- CANAL DE COMUNICACIÓN CON LA BASE DE DATOS ---
@contextmanager
def get_db_connection():
    """
    Gestor de contexto para la base de datos.
    Asegura que cada conexión se abra y se cierre correctamente,
    incluso si ocurre un error durante la ejecución.
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("🔗 Conexión abierta")
        yield conn
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        raise e
    finally:
        if conn is not None:
            conn.close()
            print("🔌 Conexión cerrada automáticamente")

# ------- RUTAS -------
# -- RUTA HTML ----
@app.route('/')
def index():
    return render_template('index.html')

# --- RUTA CSS ---
@app.route('/style.css')
def styles():
    return send_from_directory('templates', 'style.css')
# --- RUTA DE DATOS (API JSON) ---
@app.route('/api/personajes')
def api_personajes():
    """
    Esta ruta no devuelve una página web (HTML), devuelve DATOS puros.
    Es útil para que JavaScript o herramientas externas lean tu base de datos.
    """
    #
    datos = Personaje.obtener_personajes(get_db_connection)
    return jsonify(datos)

@app.route('/api/enemigos')
def api_enemigos():
    datos = Enemigo.obtener_enemigos(get_db_connection)
    return jsonify(datos)


@app.route('/api/guerreros')
def api_guerreros():
    datos = Guerrero.obtener_guerreros(get_db_connection)
    return jsonify(datos)

@app.route('/api/magos')
def api_magos():
    datos = Mago.obtener_magos(get_db_connection)
    return jsonify(datos)


@app.route('/api/inventario/')
def api_inventario():
    personaje_id = request.args.get('id')

    # IMPORTANTE: Convertir a int si existe, si no, None
    if personaje_id:
        personaje_id = int(personaje_id)

    datos = Inventario.obtener_inventario(get_db_connection, personaje_id)
    return jsonify(datos)


@app.route('/api/items/')
def api_items():
    """
    Endpoint para obtener el catálogo de items.
    Uso:
    - /api/items/ (Trae todo)
    - /api/items/?tipo=1 (Trae solo items de ese tipo)
    - /api/items/?rareza=Épico (Trae solo items épicos)
    """
    # Obtenemos los parámetros de la URL si existen
    tipo_id = request.args.get('tipo')
    rareza = request.args.get('rareza')

    # Convertimos tipo_id a entero si existe, ya que en tu SQL es un INT (FK)
    if tipo_id:
        try:
            tipo_id = int(tipo_id)
        except ValueError:
            tipo_id = None

    # Llamamos al método estático de la clase Item
    datos = Item.obtener_items(get_db_connection, tipo=tipo_id, rareza=rareza)

    return jsonify(datos)


@app.route('/api/logros/')
def api_lista_logros():
    """
    Muestra todos los logros que existen en el juego (el catálogo).
    URL: http://localhost:5000/api/logros/
    """
    datos = Logro.obtener_logros(get_db_connection)
    return jsonify(datos)


@app.route('/api/personaje/<int:personaje_id>/logros')
def api_logros_personaje(personaje_id):
    """
    Muestra solo los logros que ha desbloqueado un personaje concreto.
    URL: http://localhost:5000/api/personaje/1/logros
    """
    # Llamamos al método que usa el JOIN para traer nombre e icono
    datos = Personaje_Logro.obtener_logros_desbloqueados(get_db_connection, personaje_id)

    if not datos:
        # Si no tiene logros, devolvemos una lista vacía con un 200 OK (es normal ser un novato)
        return jsonify([])

    return jsonify(datos)

@app.route('/api/personaje/<int:id>/logros')
def api_personaje_logros(id):
    """
    URL: c
    """
    from models.Personaje_Logro import Personaje_Logro
    datos = Personaje_Logro.obtener_logros_desbloqueados(get_db_connection, id)
    return jsonify(datos)

# --- TEST DE CONEXIÓN ---
@socketio.on('connect')
def test_db_connection():
    """
    Se ejecuta automáticamente cuando un usuario abre la web.
    Realiza un 'ping' a la base de datos para confirmar que el sistema está listo.
    """
    try:
        # Usamos el context manager
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;") # Consulta de prueba rápida
                emit('status', {'msg': '✅ Conectado con éxito a la Base de Datos (PostgreSQL)'})
    except Exception as e:
        emit('status', {'msg': f'❌ Error: Base de Datos inaccesible: {str(e)}'})


# --- SOCKETS ---
@socketio.on('mejorar_habilidad')
def upgrade_skill(data):
    skill_id = data.get('id')
    emit('status', {'msg': f'Procesando mejora de habilidad ID: {skill_id}'})

@socketio.on('obtener_personajes')
def mostrar_personajes():
    # USAMOS LA CLASE.METODO y le pasamos nuestra conexión local
    datos = Personaje.obtener_personajes(get_db_connection)
    emit("personajes", datos)

if __name__ == '__main__':
    # Arranca el servidor de WebSockets
    # host='0.0.0.0' es necesario para que sea accesible desde fuera del contenedor Docker
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)