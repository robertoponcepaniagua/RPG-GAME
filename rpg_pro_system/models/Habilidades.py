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