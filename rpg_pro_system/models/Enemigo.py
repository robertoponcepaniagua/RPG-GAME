"""id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(60) NOT NULL,
    nivel       INT DEFAULT 1,
    vida_max    INT NOT NULL,
    dano_base   INT DEFAULT 5,
    exp_recom   INT DEFAULT 20,
    oro_recom   INT DEFAULT 10,
    descripcion TEXT"""

class Enemigo:
    def __init__(self, id, nombre, nivel, vida_max, dano_base, exp_recom, oro_recom, descripcion):
        self.id = id
        self.nombre = nombre
        self.nivel = nivel
        self.vida_max = vida_max
        self.dano_base = dano_base
        self.exp_recom = exp_recom
        self.oro_recom = oro_recom
        self.descripcion = descripcion

    @staticmethod
    def obtener_enemigos(get_db_connection):
        """
        Recibe la función de conexión como parámetro para evitar errores de importación.
        """
        enemigos_data = []

        # 1. Usamos tu context manager profesional
        with get_db_connection() as conexion:
            if conexion is None:
                return []

            try:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT id, nombre, nivel, vida_max, dano_base, exp_recom, oro_recom, descripcion FROM enemigos")
                    filas = cursor.fetchall()

                    for fila in filas:
                        # Desempaquetado rápido de Python (más limpio)
                        id, nombre, nivel, vida_max, dano_base, exp_recom, oro_recom, descripcion = fila

                        # Creamos el objeto
                        e = Enemigo(id, nombre, nivel, vida_max, dano_base, exp_recom, oro_recom, descripcion)

                        # Lo convertimos a diccionario (puedes usar p.__dict__ si quieres ahorrar líneas)
                        enemigos_data.append({
                            "id": e.id,
                            "nombre": e.nombre,
                            "nivel": e.nivel,
                            "vida_max": e.vida_max,
                            "dano_base": e.dano_base,
                            "exp_recom": e.exp_recom,
                            "oro_recom": e.oro_recom,
                            "descripcion": e.descripcion
                        })

                    print(f"✅ Datos recuperados: {len(enemigos_data)} enemigos.")
            except Exception as e:
                print(f"❌ Error al consultar enemigos: {e}")

        return enemigos_data