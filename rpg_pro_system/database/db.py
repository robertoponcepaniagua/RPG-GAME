from contextlib import contextmanager
from email import contentmanager

import psycopg2
import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rpguser:rpgpassword@db:5432/rpg_db")

@contextmanager
def get_db_connection():
    conn = None
    try:
        # Intentamos la conexión
        conn = psycopg2.connect(DATABASE_URL)
        print("🔗 Conexión abierta")
        yield conn

    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        print(f"DEBUG: Intentando conectar a -> {DATABASE_URL}")
        raise e  # Lanzamos el error para que Flask sepa que algo fue mal
    finally:
        if conn is not None:
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