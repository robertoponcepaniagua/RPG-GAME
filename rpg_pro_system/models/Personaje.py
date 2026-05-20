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

        Flujo:
        1. Comprueba que el personaje exista y tenga oro suficiente.
        2. Descuenta el oro en la misma transacción.
        3. Construye la instancia y llama a actualizar_estadisticas(curar_al_maximo=True),
           que ya persiste la curación completa en PostgreSQL.
        4. Devuelve los nuevos valores para que el JS actualice el HUD.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return {"ok": False, "mensaje": "Error de conexión con la base de datos."}

            try:
                with conexion.cursor() as cursor:
                    # 1. Leemos el estado actual
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

                    # 3. Descontamos el oro
                    cursor.execute(
                        "UPDATE Personajes SET oro = oro - %s WHERE id = %s",
                        (cls.COSTE_DESCANSO, id_personaje)
                    )
                    conexion.commit()

                    # 4. Creamos la instancia
                    # IMPORTANTE: Pasamos vida_max como vida_actual (y mana_max como mana_actual)
                    # para que el objeto empiece en estado "curado" en memoria.
                    personaje = cls(
                        id_personaje, nombre, nivel, exp, oro - cls.COSTE_DESCANSO,
                        vida_max, vida_max,  # <--- CORRECCIÓN AQUÍ
                        mana_max, mana_max,  # <--- CORRECCIÓN AQUÍ
                        fuerza, agilidad, inteligencia, id_raza, id_clase
                    )

                    # Esto persiste el cambio en la base de datos (PostgreSQL)
                    personaje.actualizar_estadisticas(curar_al_maximo=True)

                    return {
                        "ok": True,
                        "mensaje": f"🏕️ {nombre} descansó y recuperó todas sus fuerzas. (-{cls.COSTE_DESCANSO} oro)",
                        "personaje": {
                            "oro": personaje.oro,
                            "vida_actual": personaje.vida_actual,  # Ahora será igual a vida_max
                            "vida_max": personaje.vida_max,
                            "mana_actual": personaje.mana_actual,  # Ahora será igual a mana_max
                            "mana_max": personaje.mana_max,
                        }
                    }

            except Exception as e:
                conexion.rollback()
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


