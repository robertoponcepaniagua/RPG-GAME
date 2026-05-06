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
from models.Raza import Raza
from models.Habilidad_Requisitos import Habilidad_Requisitos
from models.Registro_Combate import Registro_Combate
from models.Tipo_Item import Tipo_Item
from models.Habilidades import Habilidades

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---- CÓDIGOS DE ESTADO ----

#Código	Categoría	Significado Simple
#200	Éxito	"¡Perfecto! Toodo funcionando."
#201	Éxito	"¡Creado! (ej. cuando creas un personaje nuevo)."
#400	Error Cliente	"Me enviaste algo mal."
#401	Error Cliente	"No tienes permiso (no estás logueado)."
#404	Error Cliente	"No lo encuentro (la URL o el ID no existen)."
#500	Error Servidor	"¡Ups! Mi código de Python explotó (un error de base de datos o sintaxis)."


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

@app.route('/api/razas/')
def api_razas():
    """
    Muestra las razas disponibles y sus estadísticas.
    URL: http://localhost:5000/api/razas/
    """
    datos = Raza.obtener_razas(get_db_connection)
    return jsonify(datos)

@app.route('/api/habilidades/<int:id>/requisitos')
def api_requisitos_habilidad(id):
    """
    Muestra qué necesitas para desbloquear la habilidad X.
    URL: http://localhost:5000/api/habilidades/5/requisitos
    """
    datos = Habilidad_Requisitos.obtener_requisitos_de_habilidad(get_db_connection, id)
    return jsonify(datos)


@app.route('/api/combate/registro', methods=['POST'])
def registrar_accion():
    """
    Registra una nueva acción de combate.
    """
    datos = request.json

    nuevo_registro = Registro_Combate(
        id_personaje=datos['id_personaje'],
        id_enemigo=datos['id_enemigo'],
        turno=datos['turno'],
        accion=datos['accion'],
        dano_infligido=datos['dano_infligido'],
        dano_received=datos['dano_received'],
        resultado=datos['resultado']
    )

    if Registro_Combate.registrar_turno(get_db_connection, nuevo_registro):
        return jsonify({"mensaje": "Acción registrada"}), 201
    return jsonify({"error": "No se pudo registrar"}), 500


@app.route('/api/personaje/<int:id>/historial')
def api_historial_combate(id):
    """
    URL: http://localhost:5000/api/personaje/1/historial
    """
    datos = Registro_Combate.obtener_historial_personaje(get_db_connection, id)
    return jsonify(datos)

@app.route('/api/items/tipos')
def api_tipos_item():
    """
    Lista todas las categorías de items existentes.
    URL: http://localhost:5000/api/items/tipos
    """
    datos = Tipo_Item.obtener_tipos(get_db_connection)
    return jsonify(datos)


@app.route('/api/habilidades')
def api_habilidades():
    """
    Obtiene el catálogo de habilidades disponibles en el juego.
    Soporta filtrado opcional por ID de clase mediante parámetros de consulta.
    Ejemplo: /api/habilidades?clase=1
    """
    try:
        # 1. Obtener el parámetro 'clase' de la URL (si existe)
        clase_id = request.args.get('clase', type=int)

        # 2. Consultar la base de datos a través del método estático
        datos = Habilidades.obtener_habilidades(get_db_connection, clase_id)

        # 3. Retornar los datos en formato JSON
        # Si no hay habilidades, devolvemos una lista vacía con status 200
        return jsonify(datos), 200

    except Exception as e:
        # Registro del error en consola para el desarrollador
        print(f"❌ Error en el endpoint /api/habilidades: {str(e)}")

        # Respuesta elegante para el cliente
        return jsonify({
            "error": "No se pudo obtener la lista de habilidades",
            "detalle": str(e) if app.debug else "Error interno del servidor"
        }), 500


# Ruta para subir nivel de personaje
@app.route('/api/personaje/subir-nivel/int ', methods=['POST'])
def api_subir_nivel():
    data = request.json
    id_personaje = data.get('id_personaje')

    # Invocamos tu método estático
    resultado = Personaje.subir_nivel(get_db_connection, id_personaje)
    return jsonify(resultado)

@app.route('/api/personaje/recompensa/<int:id_personaje>/<int:id_enemigo>', methods=['GET', 'POST'])
def api_recompensa(id_personaje, id_enemigo):
    resultado = Personaje.ganar_exp_y_oro(id_personaje, id_enemigo, get_db_connection)

    if resultado["ok"]:
        return jsonify(resultado), 200
    else:
        return jsonify(resultado), 400

# Ruta para subir nivel de habilidad
@app.route('/api/habilidad/subir-nivel', methods=['POST'])
def api_subir_habilidad():
    data = request.json
    id_personaje = data.get('id_personaje')
    id_habilidad = data.get('id_habilidad')

    resultado = Personaje.subir_nivel_habilidad(get_db_connection, id_personaje, id_habilidad)
    return jsonify(resultado)

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