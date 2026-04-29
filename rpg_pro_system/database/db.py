from contextlib import contextmanager
from email import contentmanager

import psycopg2
import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rpguser:rpgpassword@db:5432/rpg_db")


@contextmanager
def get_db_connection():
    """
    Administrador de contexto para la gestión de recursos de base de datos.
    Permite el uso de la sentencia 'with' para automatizar la apertura y cierre.
    """
    conn = None
    try:
        # Establece la conexión utilizando los parámetros definidos en DATABASE_URL.
        conn = psycopg2.connect(DATABASE_URL)
        print("🔗 Conexión abierta")

        # Cede el objeto de conexión al bloque de código solicitante y pausa la ejecución.
        yield conn

    except Exception as e:
        # Captura cualquier excepción ocurrida durante la conexión o ejecución.
        print(f"❌ Error al conectar: {e}")
        # Muestra la URL de conexión para facilitar la depuración técnica.
        print(f"DEBUG: Intentando conectar a -> {DATABASE_URL}")

        # Propaga la excepción hacia las capas superiores para notificar el fallo.
        raise e

    finally:
        # Bloque de finalización obligatoria: se ejecuta siempre, haya error o éxito.
        if conn is not None:
            # Libera el recurso y cierra la conexión con el servidor PostgreSQL.
            conn.close()
            print("🔌 Conexión cerrada automáticamente")

# PROBAR CONEXIÓN:
if __name__ == "__main__":
    try:
        conn = get_db_connection()
        print("✅ Conexión exitosa a la base de datos")
        conn.close()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")