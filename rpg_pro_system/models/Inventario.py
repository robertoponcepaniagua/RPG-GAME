from multiprocessing.forkserver import connect_to_new_process
from os import access

import flask

from database.db import get_db_connection


class Inventario:
    def __init__(self, id, id_personaje, id_item, cantidad, equipado):
        self.id = id
        self.id_personaje = id_personaje
        self.id_item = id_item
        self.cantidad = cantidad
        self.equipado = equipado

    @classmethod
    def obtener_inventario(cls, get_db_connection, personaje_id=None):
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

    @classmethod
    def add_objeto(cls, id_personaje, id_item):
        """
        METODO PARA AGREGAR UN OBJETO AL INVENTARIO DE UN PERSONAJE.
        SI YA EXISTE, SOLO AUMENTA LA CANTIDAD.
        SI NO EXISTE, CREA UN NUEVO REGISTRO.
        """
        try:
            with get_db_connection() as conexion:
                if conexion is None:
                    return {
                        "ok": False,
                        "mensaje": "No se pudo conectar con la base de datos."
                    }

                with conexion.cursor() as cursor:
                    query_update = """
                    UPDATE Inventarios SET cantidad = cantidad + 1 WHERE id_personaje = %s AND id_item = %s
                    """
                    cursor.execute(query_update, (id_personaje, id_item))

                    if cursor.rowcount == 0:
                        query_insert = """
                        INSERT into Inventarios (id_personaje, id_item, cantidad) VALUES (%s, %s, 1)
                        """
                        cursor.execute(query_insert, (id_personaje, id_item))

                    conexion.commit()
                    print(f"Objeto {id_item} agregado al inventario de {id_personaje}.")
                    return {
                        "ok": True,
                        "mensaje": f"Objeto {id_item} agregado al inventario de {id_personaje}."
                    }

        except Exception as e:
            print(f"Error al agregar objeto al inventario: {e}")
            return {
                "ok": False,
                "mensaje": f"Error al agregar objeto al inventario: {e}"
            }

    def toggle_equipar_desequipar(self):
        """
        IDEA:
        SI ESTÁ EQUIPADO, DESEQUIPAR. SI ESTÁ DESEQUIPADO, EQUIPAR.
        Versión genérica usando el ID único del registro.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return False

            try:
                with conexion.cursor() as cursor:
                    nuevo_equipado = not self.equipado

                    query = "UPDATE Inventarios SET equipado = %s WHERE id = %s"

                    cursor.execute(query, (nuevo_equipado, self.id))
                    conexion.commit()

                    self.equipado = nuevo_equipado

                    accion = "Equipado" if nuevo_equipado else "Desequipado"
                    print(f"✨ Registro {self.id} (Objeto {self.id_item}): {accion} con éxito.")
                    return True

            except Exception as e:
                print(f"❌ Error al cambiar estado de equipo: {e}")
                return False