
class Inventario:
    def __init__(self, id, id_personaje, id_item, cantidad, equipado):
        self.id = id
        self.id_personaje = id_personaje
        self.id_item = id_item
        self.cantidad = cantidad
        self.equipado = equipado

    @staticmethod
    def obtener_inventario(get_db_connection, personaje_id=None):
        """
        Recupera los registros de la tabla Inventarios.
        Si se pasa personaje_id, filtra solo los objetos de ese héroe.
        """
        inventarios_data = []

        with get_db_connection() as conexion:
            if conexion is None:
                return []

            try:
                with conexion.cursor() as cursor:
                    # Usamos un JOIN para que el objeto sea útil en el frontend
                    query = """
                            SELECT inv.id, \
                                   inv.id_personaje, \
                                   inv.id_item, \
                                   inv.cantidad, \
                                   inv.equipado,
                                   it.nombre, \
                                   it.rareza
                            FROM Inventarios inv
                                     JOIN Items it ON inv.id_item = it.id \
                            """

                    if personaje_id:
                        query += " WHERE inv.id_personaje = %s"
                        cursor.execute(query, (personaje_id,))
                    else:
                        cursor.execute(query)

                    filas = cursor.fetchall()

                    for fila in filas:
                        id_db, p_id, item_id, cant, equip, nombre_item, rareza = fila

                        # 1. Creamos la instancia usando TU constructor exacto
                        inv = Inventario(id_db, p_id, item_id, cant, equip)

                        # 2. Le inyectamos los datos extra del JOIN (dinámicamente)
                        # Esto permite que el objeto tenga nombre sin cambiar el __init__
                        inv.nombre_item = nombre_item
                        inv.rareza = rareza

                        # 3. Convertimos a diccionario para enviar al navegador
                        inventarios_data.append({
                            "id": inv.id,
                            "personaje_id": inv.id_personaje,
                            "item_id": inv.id_item,
                            "item_nombre": inv.nombre_item,
                            "cantidad": inv.cantidad,
                            "equipado": inv.equipado,
                            "rareza": inv.rareza
                        })

                    print(f"✅ Inventario cargado: {len(inventarios_data)} registros.")
            except Exception as e:
                print(f"❌ Error al consultar inventario: {e}")

        return inventarios_data