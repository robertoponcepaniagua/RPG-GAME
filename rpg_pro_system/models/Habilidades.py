class Habilidades:
    def __init__(self, id, nombre, descripcion, tipo, nivel_maximo, costo_mana, dano_base, id_clase):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.tipo = tipo
        self.nivel_maximo = nivel_maximo
        self.costo_mana = costo_mana
        self.dano_base = dano_base
        self.id_clase = id_clase

    @classmethod
    def obtener_habilidades(cls, get_db_connection, clase_id=None):
        """
        Trae el catálogo de habilidades. Puede filtrarse por clase (Guerrero, Mago, etc.)
        """
        habilidades_lista = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    query = "SELECT * FROM Habilidades"
                    params = []

                    if clase_id:
                        query += " WHERE id_clase = %s"
                        params.append(clase_id)

                    cursor.execute(query, tuple(params))
                    filas = cursor.fetchall()

                    for f in filas:
                        # Creamos el objeto Habilidad
                        h = Habilidades(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7])

                        habilidades_lista.append({
                            "id": h.id,
                            "nombre": h.nombre,
                            "descripcion": h.descripcion,
                            "tipo": h.tipo,
                            "stats": {
                                "nivel_max": h.nivel_maximo,
                                "mana": h.costo_mana,
                                "dano": h.dano_base
                            },
                            "id_clase": h.id_clase
                        })
            except Exception as e:
                print(f"❌ Error al obtener habilidades: {e}")
        return habilidades_lista

    @classmethod
    def obtener_arbol_habilidades(cls, get_db_connection, clase_id, personaje_id):
        """
        Trae TODAS las habilidades de una clase específica (catálogo)
        y les pega el nivel actual de un personaje concreto si las tiene aprendidas.
        """
        habilidades_lista = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    # LEFT JOIN: Trae todas las habilidades de la clase,
                    # y si el personaje la tiene en Personajes_Habilidades, saca su nivel.
                    # COALESCE convierte el NULL (si no la tiene) en un 0.
                    query = """
                            SELECT h.id, \
                                   h.nombre, \
                                   h.descripcion, \
                                   h.tipo, \
                                   h.nivel_maximo, \
                                   h.costo_mana, \
                                   h.dano_base, \
                                   COALESCE(ph.nivel_actual, 0) AS nivel_actual
                            FROM Habilidades h
                                     LEFT JOIN Personajes_Habilidades ph
                                               ON h.id = ph.id_habilidad AND ph.id_personaje = %s
                            WHERE h.id_clase = %s \
                            """

                    cursor.execute(query, (personaje_id, clase_id))
                    filas = cursor.fetchall()

                    for f in filas:
                        # Lo mandamos directo a la raíz (SIN el sub-objeto stats)
                        habilidades_lista.append({
                            "id": f[0],
                            "nombre": f[1],
                            "descripcion": f[2],
                            "tipo": f[3],
                            "nivel_maximo": f[4],
                            "costo_mana": f[5],
                            "dano_base": f[6],
                            "nivel_actual": f[7]  # Será 0 si no está aprendida, o el nivel real si sí
                        })
            except Exception as e:
                print(f"❌ Error al obtener el árbol de habilidades: {e}")

        return habilidades_lista