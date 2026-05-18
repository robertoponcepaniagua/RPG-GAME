from database.db import get_db_connection


class Personaje:
    def __init__(self, id, nombre, nivel, exp, oro, vida_max, vida_actual,
                 mana_max, mana_actual, fuerza, agilidad, inteligencia,
                 id_raza, id_clase, creado_en=None):
        self.id = id
        self.nombre = nombre
        self.nivel = nivel
        self.exp = exp
        self.oro = oro
        self.vida_max = vida_max
        self.vida_actual = vida_actual
        self.mana_max = mana_max
        self.mana_actual = mana_actual
        self.fuerza = fuerza
        self.agilidad = agilidad
        self.inteligencia = inteligencia
        self.id_raza = id_raza
        self.id_clase = id_clase

    @classmethod
    def obtener_personajes(cls, get_db_connection):
        """
        Recupera todos los personajes con sus nuevas estadísticas.
        """
        personajes_data = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    # Traemos TODAS las columnas que definiste en tu CREATE TABLE
                    cursor.execute("""
                                   SELECT id,
                                          nombre,
                                          nivel,
                                          exp,
                                          oro,
                                          vida_max,
                                          vida_actual,
                                          mana_max,
                                          mana_actual,
                                          fuerza,
                                          agilidad,
                                          inteligencia,
                                          id_raza,
                                          id_clase
                                   FROM Personajes
                                   """)
                    filas = cursor.fetchall()

                    for fila in filas:
                        # El asterisco (*) desempaqueta la fila automáticamente en el constructor
                        p = Personaje(*fila)
                        personajes_data.append(p.__dict__)

                print(f"✅ {len(personajes_data)} personajes cargados.")
            except Exception as e:
                print(f"❌ Error en obtener_personajes: {e}")

        return personajes_data

    @classmethod
    def comprar_obj(cls, id_personaje, id_item):
        """
        Lógica de compra completa: resta oro y añade al inventario.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return {"ok": False, "mensaje": "Error de conexión"}

            try:
                with conexion.cursor() as cursor:
                    # 1. Validar oro y precio
                    cursor.execute("SELECT oro FROM Personajes WHERE id = %s", (id_personaje,))
                    res_oro = cursor.fetchone()
                    cursor.execute("SELECT precio, nombre FROM Items WHERE id = %s", (id_item,))
                    res_item = cursor.fetchone()

                    if not res_oro or not res_item:
                        return {"ok": False, "mensaje": "Personaje o Item no encontrado"}

                    oro_actual = res_oro[0]
                    precio_item = res_item[0]
                    nombre_item = res_item[1]

                    if oro_actual < precio_item:
                        return {"ok": False, "mensaje": f"Oro insuficiente. Tienes {oro_actual} y cuesta {precio_item}"}

                    # 2. PROCESO DE COMPRA (Transacción)
                    # Restar oro
                    cursor.execute("UPDATE Personajes SET oro = oro - %s WHERE id = %s", (precio_item, id_personaje))

                    # Añadir al inventario (Update o Insert)
                    cursor.execute("""
                                   UPDATE Inventarios
                                   SET cantidad = cantidad + 1
                                   WHERE id_personaje = %s
                                     AND id_item = %s
                                   """, (id_personaje, id_item))

                    if cursor.rowcount == 0:
                        cursor.execute("""
                                       INSERT INTO Inventarios (id_personaje, id_item, cantidad, equipado)
                                       VALUES (%s, %s, 1, False)
                                       """, (id_personaje, id_item))

                    conexion.commit()
                    return {"ok": True, "mensaje": f"¡Has comprado {nombre_item}!"}

            except Exception as e:
                conexion.rollback()
                return {"ok": False, "mensaje": f"Error en la transacción: {e}"}

    @classmethod
    def ganar_exp_y_oro(cls, id_personaje, id_enemigo, get_db_connection):
        with get_db_connection() as conexion:
            try:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT exp_recom, oro_recom FROM Enemigos WHERE id = %s", (id_enemigo,))
                    recompensa = cursor.fetchone()
                    if not recompensa: return {"ok": False, "mensaje": "Enemigo no existe"}

                    cursor.execute("""
                                   UPDATE Personajes
                                   SET exp = exp + %s,
                                       oro = oro + %s
                                   WHERE id = %s
                                   """, (recompensa[0], recompensa[1], id_personaje))

                    conexion.commit()
                    return {"ok": True, "mensaje": f"Ganaste {recompensa[0]} EXP y {recompensa[1]} Oro"}
            except Exception as e:
                conexion.rollback()
                return {"ok": False, "mensaje": str(e)}

    @classmethod
    def subir_nivel(cls, get_db_connection, id_personaje):
        """
        Mantiene tu lógica de subir niveles múltiples si sobra EXP.
        """
        with get_db_connection() as conexion:
            try:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        "SELECT nombre, nivel, exp, vida_max, mana_max, fuerza, agilidad, inteligencia FROM Personajes WHERE id = %s",
                        (id_personaje,))
                    p = cursor.fetchone()
                    if not p: return {"ok": False, "mensaje": "No existe el personaje"}

                    nombre, nivel, exp, v_max, m_max, fue, agi, intel = p
                    exp_necesaria = nivel * 1000

                    if exp < exp_necesaria:
                        return {"ok": False, "mensaje": "EXP insuficiente"}

                    subidos = 0
                    while exp >= exp_necesaria:
                        exp -= exp_necesaria
                        nivel += 1
                        v_max += 20
                        m_max += 10
                        fue += 2
                        agi += 1
                        intel += 1
                        subidos += 1
                        exp_necesaria = nivel * 1000

                    cursor.execute("""
                                   UPDATE Personajes
                                   SET nivel=%s,
                                       exp=%s,
                                       vida_max=%s,
                                       vida_actual=%s,
                                       mana_max=%s,
                                       mana_actual=%s,
                                       fuerza=%s,
                                       agilidad=%s,
                                       inteligencia=%s
                                   WHERE id = %s
                                   """, (nivel, exp, v_max, v_max, m_max, m_max, fue, agi, intel, id_personaje))

                    conexion.commit()
                    return {"ok": True, "mensaje": f"¡Subiste {subidos} niveles!"}
            except Exception as e:
                conexion.rollback()
                return {"ok": False, "mensaje": str(e)}

    def actualizar_estadisticas(self):
        """
        Recalcula las estadísticas del personaje (Vida, Maná y Atributos)
        sumando los modificadores de TODOS los ítems que tiene equipados.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return {"ok": False, "mensaje": "Error de conexión"}

            try:
                with conexion.cursor() as cursor:
                    # 1. Traemos los datos BASE actuales del personaje desde la BD
                    # para evitar el bug de acumulación infinita.
                    cursor.execute("""
                                   SELECT vida_max, mana_max, fuerza, agilidad, inteligencia
                                   FROM Personajes
                                   WHERE id = %s
                                   """, (self.id,))

                    datos_base = cursor.fetchone()
                    if not datos_base:
                        return {"ok": False, "mensaje": "Personaje no encontrado"}

                    v_max_base, m_max_base, fue_base, agi_base, int_base = datos_base

                    # 2. Consultamos la SUMA de los modificadores de los ítems equipados.
                    # Usamos COALESCE para que si no hay nada equipado devuelva 0 en vez de NULL.
                    cursor.execute("""
                                   SELECT COALESCE(SUM(i.mod_vida), 0),
                                          COALESCE(SUM(i.mod_mana), 0),
                                          COALESCE(SUM(i.mod_fuerza), 0),
                                          COALESCE(SUM(i.mod_agilidad), 0),
                                          COALESCE(SUM(i.mod_inteligencia), 0)
                                   FROM Inventarios inv
                                            JOIN Items i ON inv.id_item = i.id
                                   WHERE inv.id_personaje = %s
                                     AND inv.equipado = TRUE
                                   """, (self.id,))

                    mod_vida, mod_mana, mod_fue, mod_agi, mod_int = cursor.fetchone()

                    # 3. Aplicamos los cambios al objeto en memoria (self)
                    self.fuerza = fue_base + mod_fue
                    self.agilidad = agi_base + mod_agi
                    self.inteligencia = int_base + mod_int

                    # Las estadísticas máximas aumentan con los ítems
                    self.vida_max = v_max_base + mod_vida
                    self.mana_max = m_max_base + mod_mana

                    # 4. CONTROL DE INTEGRIDAD: Evitar que la vida/maná actual superen los nuevos máximos
                    if self.vida_actual > self.vida_max:
                        self.vida_actual = self.vida_max
                    if self.mana_actual > self.mana_max:
                        self.mana_actual = self.mana_max

                    # 5. Guardamos de forma persistente los límites máximos calculados y la vida actual
                    cursor.execute("""
                                   UPDATE Personajes
                                   SET vida_max    = %s,
                                       vida_actual = %s,
                                       mana_max    = %s,
                                       mana_actual = %s
                                   WHERE id = %s
                                   """, (self.vida_max, self.vida_actual, self.mana_max, self.mana_actual, self.id))

                    conexion.commit()
                    return {"ok": True, "mensaje": "Estadísticas actualizadas con el equipamiento."}

            except Exception as e:
                conexion.rollback()
                return {"ok": False, "mensaje": f"Error al actualizar estadísticas: {e}"}
