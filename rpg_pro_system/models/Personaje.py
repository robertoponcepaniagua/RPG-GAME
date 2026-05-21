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
        # 1. Usamos 'with' porque get_db_connection es un context manager
        with get_db_connection() as conexion:
            if conexion is None:
                return {"ok": False, "mensaje": "Error de conexión con la base de datos"}

            try:
                with conexion.cursor() as cursor:
                    # 2. Validar oro y precio (¡FOR UPDATE para bloquear la fila!)
                    cursor.execute("SELECT oro FROM Personajes WHERE id = %s FOR UPDATE", (id_personaje,))
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

                    # 3. PROCESO DE COMPRA (Transacción)
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

                # 4. Guardar los cambios permanentemente
                conexion.commit()

                # 5. RETORNAR RESPUESTA
                return {
                    "ok": True,
                    "mensaje": f"¡Has comprado {nombre_item}!",
                    "oro_restante": oro_actual - precio_item
                }

            except Exception as e:
                # Si algo falla (ej. error de sintaxis SQL), revertimos la compra
                conexion.rollback()
                return {"ok": False, "mensaje": f"Error en la transacción: {str(e)}"}

            # Ya NO necesitamos el bloque `finally` con `conexion.close()`.
            # Al salir del bloque `with get_db_connection()`, Python la cierra automáticamente.

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
        Sube de nivel al personaje si tiene suficiente EXP, incrementando sus estadísticas base.
        Devuelve el objeto actualizado para que el JS renderice el HUD correctamente.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return {"ok": False, "mensaje": "Error de conexión con la base de datos"}
            try:
                with conexion.cursor() as cursor:
                    # 1. Recuperamos los atributos actuales
                    cursor.execute("""
                                   SELECT nombre,
                                          nivel,
                                          exp,
                                          vida_max,
                                          mana_max,
                                          fuerza,
                                          agilidad,
                                          inteligencia
                                   FROM Personajes
                                   WHERE id = %s
                                   """, (id_personaje,))

                    p = cursor.fetchone()
                    if not p:
                        return {"ok": False, "mensaje": "No existe el personaje"}

                    nombre, nivel, exp, v_max, m_max, fue, agi, intel = p
                    exp_necesaria = nivel * 1000

                    # Guard Clause
                    if exp < exp_necesaria:
                        return {"ok": False, "mensaje": "EXP insuficiente para subir de nivel"}

                    # 2. Bucle de subida de niveles múltiples
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

                    # 3. Guardamos los nuevos atributos base
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

                    # 💡 TIP: Forzamos la actualización de equipamiento antes de responder al JS
                    personaje_instancia = cls(
                        id_personaje, nombre, nivel, exp, 0, v_max, v_max,
                        m_max, m_max, fue, agi, intel, None, None
                    )
                    personaje_instancia.actualizar_estadisticas()

                    # 4. CONSTRUIMOS LA RESPUESTA QUE BUSCA TU JS
                    # Tu JS espera: datos.nivel_actual, datos.vida_max, datos.vida_actual,
                    # datos.fuerza, datos.agilidad, datos.inteligencia, datos.exp_restante, datos.exp_para_siguiente_nivel
                    return {
                        "ok": True,
                        "mensaje": f"¡Enhorabuena! {nombre} subió {subidos} nivel(es).",
                        "personaje": {
                            "nivel_actual": personaje_instancia.nivel,
                            "vida_max": personaje_instancia.vida_max,
                            "vida_actual": personaje_instancia.vida_actual,
                            "fuerza": personaje_instancia.fuerza,
                            "agilidad": personaje_instancia.agilidad,
                            "inteligencia": personaje_instancia.inteligencia,
                            "exp_restante": personaje_instancia.exp,
                            "exp_para_siguiente_nivel": personaje_instancia.nivel * 1000
                        }
                    }

            except Exception as e:
                conexion.rollback()
                return {"ok": False, "mensaje": f"Error al subir de nivel: {str(e)}"}

    COSTE_DESCANSO = 50  # una sola constante para cambiarla fácilmente

    @classmethod
    def descansar(cls, get_db_connection, id_personaje):
        """
        Descansa en la posada: cuesta COSTE_DESCANSO de oro y restaura
        vida y maná al máximo (incluyendo bonus de equipo activo).
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return {"ok": False, "mensaje": "Error de conexión con la base de datos."}

            try:
                with conexion.cursor() as cursor:
                    # 1. Leemos el estado actual del personaje
                    cursor.execute("""
                                   SELECT nombre,
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
                                   WHERE id = %s
                                   """, (id_personaje,))

                    fila = cursor.fetchone()
                    if not fila:
                        return {"ok": False, "mensaje": "Personaje no encontrado."}

                    (nombre, nivel, exp, oro,
                     vida_max, vida_actual,
                     mana_max, mana_actual,
                     fuerza, agilidad, inteligencia,
                     id_raza, id_clase) = fila

                    # 2. Validación de oro
                    if oro < cls.COSTE_DESCANSO:
                        return {
                            "ok": False,
                            "mensaje": f"Necesitas {cls.COSTE_DESCANSO} de oro para descansar. Tienes {oro}."
                        }

                    # 3.
                    # Hacemos todo en una sola transacción y al final guardamos todo junto.
                    nuevo_oro = oro - cls.COSTE_DESCANSO

                    # 4. 🔥 CORRECCIÓN 2: Actualizamos Oro, Vida y Maná de un solo golpe en la BD
                    cursor.execute("""
                                   UPDATE Personajes
                                   SET oro         = %s,
                                       vida_actual = vida_max,
                                       mana_actual = mana_max
                                   WHERE id = %s
                                   """, (nuevo_oro, id_personaje))

                    # 5. Creamos la instancia en memoria con los datos idénticos a la BD
                    personaje = cls(
                        id_personaje, nombre, nivel, exp, nuevo_oro,
                        vida_max, vida_max,  # Curado al máximo
                        mana_max, mana_max,  # Curado al máximo
                        fuerza, agilidad, inteligencia, id_raza, id_clase
                    )

                    # 6. Confirmamos TODA la transacción junta (Pagar + Curar)
                    conexion.commit()

                    return {
                        "ok": True,
                        "mensaje": f"🏕️ {nombre} descansó y recuperó todas sus fuerzas. (-{cls.COSTE_DESCANSO} oro)",
                        "personaje": {
                            "oro": personaje.oro,
                            "vida_actual": personaje.vida_actual,
                            "vida_max": personaje.vida_max,
                            "mana_actual": personaje.mana_actual,
                            "mana_max": personaje.mana_max,
                        }
                    }

            except Exception as e:
                conexion.rollback()
                print(f"❌ Error crítico en descansar: {e}")
                return {"ok": False, "mensaje": f"Error al descansar: {str(e)}"}


    # FALTA AÑADIR EL REQUISITO DE EXPERIENCIA PARA SUBIR DE NIVEL LA HABILIDAD, PARA GANAR EXP EN LA HABILIDAD HE PENSADO QUE AL USARLA GANE 10 DE EXP POR CADA USO
    @classmethod
    def subir_nivel_habilidad(cls, get_db_connection, id_personaje, id_habilidad):
        """
        Sube el nivel de una habilidad del personaje.
        Si no la tiene, la desbloquea (Nivel 1) si cumple los requisitos.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:

                    # ── 1. Buscamos primero si la habilidad existe en el juego ──
                    cur.execute("""
                                SELECT nombre, nivel_maximo
                                FROM Habilidades
                                WHERE id = %s
                                """, (id_habilidad,))

                    fila_habilidad = cur.fetchone()
                    if not fila_habilidad:
                        return {
                            "ok": False,
                            "mensaje": f"La habilidad con ID {id_habilidad} no existe en el juego."
                        }

                    nombre_habilidad, nivel_maximo = fila_habilidad

                    # ── 2. Estado actual del personaje (Bloqueo para evitar exploits) ──
                    cur.execute("""
                                SELECT nivel_actual
                                FROM Personajes_Habilidades
                                WHERE id_personaje = %s
                                  AND id_habilidad = %s
                                    FOR UPDATE
                                """, (id_personaje, id_habilidad))

                    fila_personaje = cur.fetchone()

                    # Si existe, leemos su nivel. Si no, asumimos que está en nivel 0 (no desbloqueada)
                    existe_registro = fila_personaje is not None
                    nivel_actual = fila_personaje[0] if existe_registro else 0

                    # ── 3. ¿Ya está al máximo? ───────────────────────────────────
                    if nivel_actual >= nivel_maximo:
                        return {
                            "ok": False,
                            "mensaje": f"'{nombre_habilidad}' ya está en su nivel máximo ({nivel_maximo})."
                        }

                    # ── 4. Comprobación de requisitos previos ────────────────────
                    cur.execute("""
                                SELECT hr.id_requisito, hr.nivel_requisito_necesario, COALESCE(ph.nivel_actual, 0)
                                FROM Habilidades_Requisitos hr
                                         LEFT JOIN Personajes_Habilidades ph
                                                   ON ph.id_habilidad = hr.id_requisito AND ph.id_personaje = %s
                                WHERE hr.id_habilidad = %s
                                  AND COALESCE(ph.nivel_actual, 0) < hr.nivel_requisito_necesario
                                """, (id_personaje, id_habilidad))

                    requisitos_no_cumplidos = cur.fetchall()

                    if requisitos_no_cumplidos:
                        id_req, nivel_requerido, nivel_actual_req = requisitos_no_cumplidos[0]
                        return {
                            "ok": False,
                            "mensaje": (
                                f"Requisito no cumplido: "
                                f"habilidad {id_req} necesita nivel {nivel_requerido} "
                                f"(tienes nivel {nivel_actual_req})."
                            )
                        }

                    # ── 5. Guardar cambios (INSERT si es nueva, UPDATE si ya existía) ──
                    if not existe_registro:
                        # Desbloqueo inicial (Pasa de no existir a Nivel 1)
                        cur.execute("""
                                    INSERT INTO Personajes_Habilidades (id_personaje, id_habilidad, nivel_actual)
                                    VALUES (%s, %s, 1)
                                    """, (id_personaje, id_habilidad))
                    else:
                        # Subida de nivel normal
                        cur.execute("""
                                    UPDATE Personajes_Habilidades
                                    SET nivel_actual = nivel_actual + 1
                                    WHERE id_personaje = %s
                                      AND id_habilidad = %s
                                    """, (id_personaje, id_habilidad))

                    conn.commit()

                    return {
                        "ok": True,
                        "mensaje": f"✅ '{nombre_habilidad}' subida al nivel {nivel_actual + 1}.",
                        "nivel_nuevo": nivel_actual + 1
                    }

        except Exception as e:
            print(f"❌ Error en subir_nivel_habilidad: {e}")
            return {"ok": False, "mensaje": f"Error del servidor: {str(e)}"}

    @staticmethod
    def obtener_estadisticas_personaje(get_db_connection, id_personaje):
        """
        Recupera las estadísticas directamente de la tabla Personajes,
        forzando autocommit para evitar leer datos cacheados por transacciones concurrentes.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return None
            try:
                # 🔥 LA CLAVE COMPLETA: Forzamos a que la lectura sea en tiempo real directo
                # Evita que Psycopg2 use una "foto aislada" vieja de la base de datos
                conexion.autocommit = True

                with conexion.cursor() as cursor:
                    cursor.execute("""
                                   SELECT p.vida_max,
                                          p.vida_actual,
                                          p.mana_max,
                                          p.mana_actual,
                                          p.fuerza,
                                          p.agilidad,
                                          p.inteligencia,
                                          c.recurso_primario
                                   FROM Personajes p
                                            JOIN Clases_RPG c ON p.id_clase = c.id
                                   WHERE p.id = %s;
                                   """, (id_personaje,))

                    fila = cursor.fetchone()

                    if fila:
                        return {
                            "vida_max": fila[0],
                            "vida_actual": fila[1],
                            "mana_max": fila[2],
                            "mana_actual": fila[3],
                            "fuerza": fila[4],
                            "agilidad": fila[5],
                            "inteligencia": fila[6],
                            "recurso_primario": fila[7] if fila[7] else "Mana"
                        }
                    return None
            except Exception as e:
                print(f"❌ Error en obtener_estadisticas_personaje: {e}")
                return None

    @classmethod
    def sincronizar_personaje(cls, get_db_connection, id_personaje):
        """
        Recalcula TODOS los stats incluyendo: Vida, Mana, Fuerza, Agilidad, Inteligencia.
        Usa lógica de actualización condicional para evitar bucles o escrituras innecesarias.
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Calculamos todo en una sola consulta robusta
                cur.execute("""
                            SELECT
                                -- Fórmulas base + Raza + Equipo
                                (100 + ((p.nivel - 1) * 15) + r.mod_vida + COALESCE(SUM(i.mod_vida), 0))       as v_vida,
                                (50 + ((p.nivel - 1) * 10) + r.mod_mana +
                                 COALESCE(SUM(i.mod_mana), 0))                                                 as v_mana,
                                (10 + ((p.nivel - 1) * 2) + r.mod_fuerza + COALESCE(SUM(i.mod_fuerza), 0))     as v_fue,
                                (10 + ((p.nivel - 1) * 2) + r.mod_agilidad + COALESCE(SUM(i.mod_agilidad), 0)) as v_agi,
                                (10 + ((p.nivel - 1) * 2) + r.mod_inteligencia +
                                 COALESCE(SUM(i.mod_inteligencia), 0))                                         as v_int
                            FROM Personajes p
                                     JOIN Razas r ON p.id_raza = r.id
                                     LEFT JOIN Inventarios inv ON p.id = inv.id_personaje AND inv.equipado = TRUE
                                     LEFT JOIN Items i ON inv.id_item = i.id
                            WHERE p.id = %s
                            GROUP BY p.nivel, r.mod_vida, r.mod_mana, r.mod_fuerza, r.mod_agilidad, r.mod_inteligencia
                            """, (id_personaje,))

                stats = cur.fetchone()
                if not stats: return None

                v_vida, v_mana, v_fue, v_agi, v_int = stats

                # 2. UPDATE "Inteligente": Solo escribe si algo cambió realmente
                cur.execute("""
                            UPDATE Personajes
                            SET vida_max     = %s,
                                mana_max     = %s,
                                fuerza       = %s,
                                agilidad     = %s,
                                inteligencia = %s,
                                vida_actual  = CASE WHEN vida_actual > %s THEN %s ELSE vida_actual END,
                                mana_actual  = CASE WHEN mana_actual > %s THEN %s ELSE mana_actual END
                            WHERE id = %s
                              AND (vida_max != %s OR mana_max != %s OR fuerza != %s OR agilidad != %s OR inteligencia != %s)
                            """, (v_vida, v_mana, v_fue, v_agi, v_int,
                                  v_vida, v_vida, v_mana, v_mana,
                                  id_personaje,
                                  v_vida, v_mana, v_fue, v_agi, v_int))

                conn.commit()
                return {"vida": v_vida, "mana": v_mana, "fuerza": v_fue, "agilidad": v_agi, "inteligencia": v_int}
