class Tipo_Item:
    def __init__(self, id, nombre):
        self.id = id
        self.nombre = nombre

    @classmethod
    def obtener_tipos(get_db_connection):
        """
        Recupera todos los tipos de items disponibles (Arma, Poción, etc.)
        """
        tipos_data = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT id, nombre FROM Tipos_Item ORDER BY nombre ASC")
                    filas = cursor.fetchall()

                    for fila in filas:
                        t_id, nom = fila
                        # Creamos la instancia
                        tipo_obj = Tipo_Item(t_id, nom)
                        
                        # Añadimos al listado para el JSON
                        tipos_data.append({
                            "id": tipo_obj.id,
                            "nombre": tipo_obj.nombre
                        })
            except Exception as e:
                print(f"❌ Error al consultar tipos de item: {e}")
        return tipos_data