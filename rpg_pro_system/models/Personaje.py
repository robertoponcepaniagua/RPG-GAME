from database.db import get_db_connection


class Personaje:
    def __init__(self, id, nombre, nivel, exp, oro, vida_actual, id_raza, id_clase):
        self.id = id
        self.nombre = nombre
        self.nivel = nivel
        self.exp = exp
        self.oro = oro
        self.vida_actual = vida_actual
        self.id_raza = id_raza
        self.id_clase = id_clase

    @staticmethod
    def obtener_personajes(get_db_connection):
        """
        Recibe la función de conexión como parámetro para evitar errores de importación.
        """
        personajes_data = []

        # 1. Usamos tu context manager profesional
        with get_db_connection() as conexion:
            if conexion is None:
                return []

            try:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT id, nombre, nivel, exp, oro, vida_actual, id_raza, id_clase FROM personajes")
                    filas = cursor.fetchall()

                    for fila in filas:
                        # Desempaquetado rápido de Python (más limpio)
                        id_db, nombre, nivel, exp, oro, vida, raza, clase = fila

                        # Creamos el objeto
                        p = Personaje(id_db, nombre, nivel, exp, oro, vida, raza, clase)

                        # Lo convertimos a diccionario (puedes usar p.__dict__ si quieres ahorrar líneas)
                        personajes_data.append({
                            "id": p.id,
                            "nombre": p.nombre,
                            "nivel": p.nivel,
                            "exp": p.exp,
                            "oro": p.oro,
                            "vida_actual": p.vida_actual,
                            "id_raza": p.id_raza,
                            "id_clase": p.id_clase
                        })

                    print(f"✅ Datos recuperados: {len(personajes_data)} personajes.")
            except Exception as e:
                print(f"❌ Error al consultar personajes: {e}")

        return personajes_data

    @staticmethod
    def obtener_habilidades_por_personaje(get_db_connection, id_personaje):
        """
        Devuelve la lista de habilidades que un personaje ha aprendido,
        junto con su nivel_actual y exp_habilidad.
        Hace JOIN entre Personajes_Habilidades y Habilidades para incluir
        el nombre, descripción, tipo, costo de maná y daño base.
        """
        habilidades_personaje = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    # SQL con JOIN para traer los datos de la habilidad y el nivel del personaje
                    query = """
                            SELECT h.id, \
                                   h.nombre, \
                                   h.descripcion, \
                                   h.tipo,
                                   ph.nivel_actual, \
                                   h.nivel_maximo, \
                                   h.costo_mana, \
                                   h.dano_base
                            FROM Habilidades h
                                     INNER JOIN Personaje_Habilidades ph ON h.id = ph.id_habilidad
                            WHERE ph.id_personaje = %s \
                            """
                    cursor.execute(query, (id_personaje,))
                    filas = cursor.fetchall()

                    for f in filas:
                        habilidades_personaje.append({
                            "id": f[0],
                            "nombre": f[1],
                            "descripcion": f[2],
                            "tipo": f[3],
                            "nivel_progreso": f"{f[4]}/{f[5]}",  # Ejemplo: "3/5"
                            "nivel_actual": f[4],
                            "costo_mana": f[6],
                            "dano": f[7]
                        })
            except Exception as e:
                print(f"❌ Error al obtener habilidades del personaje {id_personaje}: {e}")
        return habilidades_personaje
