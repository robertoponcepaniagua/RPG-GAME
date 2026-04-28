import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ.get("DB_NAME", "rpg_db"),
        user=os.environ.get("DB_USER", "rpguser"),
        password=os.environ.get("DB_PASSWORD", "rpgpassword")
    )

# PROBAR CONEXIÓN: docker compose exec app python database/db.py
if __name__ == "__main__":
    try:
        conn = get_connection()
        print("✅ Conexión exitosa a la base de datos")
        conn.close()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")