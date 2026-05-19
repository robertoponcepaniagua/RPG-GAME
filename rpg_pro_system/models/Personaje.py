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
    def obtener_estadisticas_personaje(cls, id_personaje, get_db_connection):
        """
        Recupera el personaje cruzando datos con su Raza y Clase_RPG para calcular
        las estadísticas finales aplicando la regla de diseño por nivel.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return None
            try:
                with conexion.cursor() as cursor:
                    # 🌟 JOIN exacto usando la tabla 'Clases_RPG' de tu script
                    cursor.execute("""
                                   SELECT p.nombre,
                                          p.nivel,
                                          p.exp,
                                          p.oro,
                                          p.vida_actual,
                                          p.vida_max,
                                          p.mana_actual,
                                          p.mana_max,
                                          p.fuerza,
                                          p.agilidad,
                                          p.inteligencia,
                                          r.mod_vida,
                                          r.mod_mana,
                                          r.mod_fuerza,
                                          r.mod_agilidad,
                                          r.mod_inteligencia,
                                          c.factor_dano,
                                          c.dado_vida,
                                          c.recurso_primario
                                   FROM Personajes p
                                            LEFT JOIN Razas r ON p.id_raza = r.id
                                            LEFT JOIN Clases_RPG c ON p.id_clase = c.id
                                   WHERE p.id = %s
                                   """, (id_personaje,))

                    fila = cursor.fetchone()

                    if not fila:
                        return None

                    # Desempaquetado seguro de los datos devueltos por PostgreSQL
                    (nombre, nivel, exp, oro, vida_actual, vida_max_base, mana_actual, mana_max_base,
                     fuerza_base, agilidad_base, inteligencia_base,
                     mod_vida, mod_mana, mod_fuerza, mod_agilidad, mod_inteligencia,
                     factor_dano, dado_vida, recurso_primario) = fila

                    # Guardas y valores por defecto (Evitamos errores si hay valores NULL en cascada)
                    mod_vida = int(mod_vida or 0)
                    mod_mana = int(mod_mana or 0)
                    mod_fuerza = int(mod_fuerza or 0)
                    mod_agilidad = int(mod_agilidad or 0)
                    mod_inteligencia = int(mod_inteligencia or 0)

                    # factor_dano viene de PostgreSQL como Decimal/Numeric, lo pasamos a float
                    factor_dano = float(factor_dano or 1.0)
                    dado_vida = int(dado_vida or 8)
                    nivel_int = int(nivel or 1)

                    # 🧮 NUEVAS FÓRMULAS DE BALANCEO S-RPG (Implementación Fácil)
                    # REGLA: Base + Mod_Raza + (Dado_Vida * Nivel)

                    # 1. Cálculo de Atributos Máximos Balanceados
                    vida_max_final = int(vida_max_base or 10) + mod_vida + (dado_vida * nivel_int)

                    # El Maná escala por nivel si la clase usa activamente el sistema de magia
                    if recurso_primario == 'Maná' or recurso_primario == 'Mana':
                        mana_max_final = int(mana_max_base or 0) + mod_mana + (dado_vida * nivel_int)
                    else:
                        mana_max_final = int(mana_max_base or 0) + mod_mana

                    # 2. Control de desbordamiento (Evitamos que la vida actual supere al nuevo máximo)
                    vida_act_final = min(int(vida_actual or 0), vida_max_final)
                    mana_act_final = min(int(mana_actual or 0), mana_max_final)

                    # 3. Escalado de Atributos Principales con el factor_dano (fuerza, agilidad, inteligencia)
                    fuerza_final = int((int(fuerza_base or 10) + mod_fuerza) * factor_dano)
                    agilidad_final = int((int(agilidad_base or 10) + mod_agilidad) * factor_dano)
                    inteligencia_final = int((int(inteligencia_base or 10) + mod_inteligencia) * factor_dano)

                    # Estructura limpia lista para ser serializada en JSON hacia tu frontend
                    return {
                        "id": id_personaje,
                        "nombre": nombre,
                        "nivel": nivel_int,
                        "exp": int(exp or 0),
                        "oro": int(oro or 0),
                        "vida_actual": vida_act_final,
                        "vida_max": vida_max_final,
                        "mana_actual": mana_act_final,
                        "mana_max": mana_max_final,
                        "fuerza": fuerza_final,
                        "agilidad": agilidad_final,
                        "inteligencia": inteligencia_final,
                        "recurso_primario": recurso_primario
                    }
            except Exception as e:
                print(f"❌ Error en el cálculo RPG / Consulta SQL: {e}")
                return None
            
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

    def actualizar_estadisticas(self, curar_al_maximo=False):
        """
        Recalcula los atributos del personaje en memoria.
        Por defecto curar_al_maximo es False, evitando curar al cargar la página.
        """
        with get_db_connection() as conexion:
            if conexion is None: return {"ok": False, "mensaje": "Error de conexión"}

            try:
                with conexion.cursor() as cursor:
                    # 1. Obtenemos datos (base + mods)
                    # ... [Aquí mantienes tus consultas SELECT de siempre] ...

                    # 2. Asignamos los Máximos calculados
                    self.vida_max = v_base + mod_vida
                    self.mana_max = m_base + mod_mana

                    # 3. LÓGICA BLINDADA: Solo curamos si es explícito
                    if curar_al_maximo:
                        # Esto solo pasa al descansar
                        self.vida_actual = self.vida_max
                        self.mana_actual = self.mana_max
                    else:
                        # MODO SINCRONIZACIÓN: Solo ajustamos si el máximo bajó
                        # (ej: si el jugador se quitó una pieza de equipo)
                        if self.vida_actual > self.vida_max:
                            self.vida_actual = self.vida_max
                        if self.mana_actual > self.mana_max:
                            self.mana_actual = self.mana_max
                        # SI EL PERSONAJE ESTÁ HERIDO (vida_actual < vida_max),
                        # NO HACEMOS NADA. Mantenemos la herida intacta.

                    # 4. Persistencia
                    cursor.execute("""
                                   UPDATE Personajes
                                   SET vida_actual = %s,
                                       mana_actual = %s
                                   WHERE id = %s
                                   """, (self.vida_actual, self.mana_actual, self.id))

                    conexion.commit()
                    return {"ok": True, "mensaje": "Stats sincronizadas."}

            except Exception as e:
                conexion.rollback()
                return {"ok": False, "mensaje": str(e)}

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
