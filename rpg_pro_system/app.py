import os
from contextlib import contextmanager

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import psycopg2

from models.Enemigo import Enemigo
from models.Guerrero import Guerrero
from models.Habilidad_Requisitos import Habilidad_Requisitos
from models.Habilidades import Habilidades
from models.Inventario import Inventario
from models.Item import Item
from models.Logro import Logro
from models.Mago import Mago
from models.Personaje import Personaje
from models.Personaje_Logro import Personaje_Logro
from models.Raza import Raza
from models.Registro_Combate import Registro_Combate
from models.Tipo_Item import Tipo_Item

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rpguser:rpgpassword@db:5432/rpg_db"
)

# Códigos de estado HTTP usados en esta API:
#   200  Éxito            Respuesta correcta.
#   201  Creado           Recurso creado (ej. nuevo personaje).
#   400  Error cliente    Datos enviados incorrectos o incompletos.
#   404  No encontrado    La URL o el ID no existen.
#   500  Error servidor   Fallo interno (base de datos, sintaxis, etc.).


# =============================================================================
# CONEXIÓN A LA BASE DE DATOS
# =============================================================================

@contextmanager
def get_db_connection():
    """Abre y cierra la conexión a PostgreSQL de forma segura."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("🔗 Conexión abierta")
        yield conn
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()
            print("🔌 Conexión cerrada")


# =============================================================================
# VISTAS HTML
# =============================================================================

@app.route("/")
def index():
    return render_template("index.html")


# =============================================================================
# API — PERSONAJES
# =============================================================================

@app.route("/api/personajes")
def api_personajes():
    datos = Personaje.obtener_personajes(get_db_connection)
    return jsonify(datos)


@app.route("/api/guerreros")
def api_guerreros():
    datos = Guerrero.obtener_guerreros(get_db_connection)
    return jsonify(datos)


@app.route("/api/magos")
def api_magos():
    datos = Mago.obtener_magos(get_db_connection)
    return jsonify(datos)


@app.route("/api/personajes/<int:id_personaje>/estadisticas")
def api_estadisticas_personaje(id_personaje):
    stats = Personaje.obtener_estadisticas_personaje(id_personaje, get_db_connection)
    if not stats:
        return jsonify({"ok": False, "mensaje": "Personaje no encontrado"}), 404
    return jsonify(stats), 200


@app.route("/api/personaje/subir-nivel", methods=["POST"])
def api_subir_nivel():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "mensaje": "No se recibieron datos"}), 400

    id_personaje = data.get("id_personaje")
    resultado = Personaje.subir_nivel(get_db_connection, id_personaje)
    return jsonify(resultado)


@app.route("/api/personaje/descansar", methods=["POST"])
def api_descansar():
    """Restaura vida y maná del personaje a cambio de oro."""
    data = request.get_json()
    if not data or "id_personaje" not in data:
        return jsonify({"ok": False, "mensaje": "Falta id_personaje en el cuerpo"}), 400

    resultado = Personaje.descansar(get_db_connection, data["id_personaje"])
    status = 200 if resultado["ok"] else 400
    return jsonify(resultado), status


# =============================================================================
# API — ENEMIGOS
# =============================================================================

@app.route("/api/enemigos")
def api_enemigos():
    datos = Enemigo.obtener_enemigos(get_db_connection)
    return jsonify(datos)


# =============================================================================
# API — COMBATE
# =============================================================================

@app.route("/api/combate/registro", methods=["POST"])
def api_registrar_accion():
    """Registra una acción de combate (un turno)."""
    datos = request.json

    nuevo_registro = Registro_Combate(
        id_personaje=datos["id_personaje"],
        id_enemigo=datos["id_enemigo"],
        turno=datos["turno"],
        accion=datos["accion"],
        dano_infligido=datos["dano_infligido"],
        dano_received=datos["dano_received"],
        resultado=datos["resultado"],
    )

    if Registro_Combate.registrar_turno(get_db_connection, nuevo_registro):
        return jsonify({"mensaje": "Acción registrada"}), 201
    return jsonify({"error": "No se pudo registrar"}), 500


@app.route("/api/personaje/<int:id>/historial")
def api_historial_combate(id):
    datos = Registro_Combate.obtener_historial_personaje(get_db_connection, id)
    return jsonify(datos)


@app.route("/api/personaje/recompensa/<int:id_personaje>/<int:id_enemigo>", methods=["GET", "POST"])
def api_recompensa(id_personaje, id_enemigo):
    """Otorga experiencia y oro al personaje tras derrotar a un enemigo."""
    resultado = Personaje.ganar_exp_y_oro(id_personaje, id_enemigo, get_db_connection)
    status = 200 if resultado["ok"] else 400
    return jsonify(resultado), status


# =============================================================================
# API — HABILIDADES
# =============================================================================

@app.route("/api/habilidades")
def api_habilidades():
    """
    Catálogo de habilidades. Admite filtrado por clase:
    /api/habilidades?clase=1
    """
    try:
        clase_id = request.args.get("clase", type=int)
        datos = Habilidades.obtener_habilidades(get_db_connection, clase_id)
        return jsonify(datos), 200
    except Exception as e:
        print(f"❌ Error en /api/habilidades: {e}")
        return jsonify({
            "error": "No se pudo obtener la lista de habilidades",
            "detalle": str(e) if app.debug else "Error interno del servidor",
        }), 500


@app.route("/api/habilidades/<int:id>/requisitos")
def api_requisitos_habilidad(id):
    """Devuelve los requisitos necesarios para desbloquear una habilidad."""
    datos = Habilidad_Requisitos.obtener_requisitos_de_habilidad(get_db_connection, id)
    return jsonify(datos)


@app.route("/api/personajes/arbol-habilidades")
def api_arbol_habilidades():
    """
    Árbol de habilidades de un personaje según su clase.
    Requiere: ?clase_id=X&personaje_id=Y
    """
    clase_id = request.args.get("clase_id")
    personaje_id = request.args.get("personaje_id")

    if not clase_id or not personaje_id:
        return jsonify({
            "error": "Faltan parámetros: clase_id y personaje_id son obligatorios"
        }), 400

    habilidades = Habilidades.obtener_arbol_habilidades(get_db_connection, clase_id, personaje_id)
    return jsonify(habilidades)


@app.route("/api/habilidad/subir-nivel", methods=["POST"])
def api_subir_habilidad():
    data = request.json
    id_personaje = data.get("id_personaje")
    id_habilidad = data.get("id_habilidad")
    resultado = Personaje.subir_nivel_habilidad(get_db_connection, id_personaje, id_habilidad)
    return jsonify(resultado)


# =============================================================================
# API — INVENTARIO E ITEMS
# =============================================================================

@app.route("/api/inventario/")
def api_inventario():
    """
    Inventario de un personaje.
    /api/inventario/?id=3
    """
    personaje_id = request.args.get("id", type=int)
    datos = Inventario.obtener_inventario(get_db_connection, personaje_id)
    return jsonify(datos)


@app.route("/api/inventario/add/<int:id_personaje>/<int:id_item>", methods=["GET", "POST"])
def api_add_item_inventario(id_personaje, id_item):
    resultado = Inventario.add_objeto(id_personaje, id_item)
    status = 200 if resultado["ok"] else 400
    return jsonify(resultado), status


@app.route("/api/inventario/toggle/<int:inv_id>", methods=["POST"])
def api_toggle_equipar(inv_id):
    """Alterna el estado equipado / desequipado de un registro de inventario."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_personaje, id_item, cantidad, equipado "
                    "FROM Inventarios WHERE id = %s",
                    (inv_id,),
                )
                fila = cur.fetchone()

        if not fila:
            return jsonify({
                "ok": False,
                "mensaje": f"Registro de inventario {inv_id} no encontrado.",
            }), 404

        inv = Inventario(*fila)
        if not inv.toggle_equipar_desequipar():
            return jsonify({
                "ok": False,
                "mensaje": "No se pudo actualizar el estado en la base de datos.",
            }), 500

        accion = "Equipado" if inv.equipado else "Desequipado"
        return jsonify({
            "ok": True,
            "equipado": inv.equipado,
            "mensaje": f"✅ {accion} con éxito.",
        }), 200

    except Exception as e:
        print(f"❌ Error en toggle_equipar: {e}")
        return jsonify({"ok": False, "mensaje": f"Error del servidor: {str(e)}"}), 500


@app.route("/api/items/")
def api_items():
    """
    Catálogo de items. Admite filtros:
    /api/items/?tipo=1
    /api/items/?rareza=Épico
    """
    tipo_id = request.args.get("tipo", type=int)
    rareza = request.args.get("rareza")
    datos = Item.obtener_items(get_db_connection, tipo=tipo_id, rareza=rareza)
    return jsonify(datos)


@app.route("/api/items/tipos")
def api_tipos_item():
    datos = Tipo_Item.obtener_tipos(get_db_connection)
    return jsonify(datos)


# =============================================================================
# API — LOGROS Y RAZAS
# =============================================================================

@app.route("/api/logros/")
def api_lista_logros():
    """Catálogo completo de logros del juego."""
    datos = Logro.obtener_logros(get_db_connection)
    return jsonify(datos)


@app.route("/api/personaje/<int:personaje_id>/logros")
def api_logros_personaje(personaje_id):
    """Logros desbloqueados por un personaje concreto."""
    datos = Personaje_Logro.obtener_logros_desbloqueados(get_db_connection, personaje_id)
    return jsonify(datos if datos else [])


@app.route("/api/razas/")
def api_razas():
    datos = Raza.obtener_razas(get_db_connection)
    return jsonify(datos)


# =============================================================================
# WEBSOCKETS
# =============================================================================

@socketio.on("connect")
def on_connect():
    """Ping a la base de datos al conectar un cliente."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        emit("status", {"msg": "✅ Conectado con éxito a la Base de Datos (PostgreSQL)"})
    except Exception as e:
        emit("status", {"msg": f"❌ Base de Datos inaccesible: {str(e)}"})


@socketio.on("mejorar_habilidad")
def on_mejorar_habilidad(data):
    skill_id = data.get("id")
    emit("status", {"msg": f"Procesando mejora de habilidad ID: {skill_id}"})


@socketio.on("obtener_personajes")
def on_obtener_personajes():
    datos = Personaje.obtener_personajes(get_db_connection)
    emit("personajes", datos)


# =============================================================================
# ARRANQUE
# =============================================================================

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)