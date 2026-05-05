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

    @staticmethod
    def subir_nivel(get_db_connection, id_personaje):
        """
        Sube de nivel a un personaje si tiene experiencia suficiente.

        Fórmula usada:
        - EXP necesaria = nivel_actual * 1000

        Mejoras por nivel:
        - vida_max +20
        - vida_actual se cura al máximo
        - mana_max +10
        - mana_actual se recupera al máximo
        - fuerza +2
        - agilidad +1
        - inteligencia +1
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return {
                    "ok": False,
                    "mensaje": "No se pudo conectar con la base de datos."
                }

            try:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id,
                               nombre,
                               nivel,
                               exp,
                               vida_max,
                               vida_actual,
                               mana_max,
                               mana_actual,
                               fuerza,
                               agilidad,
                               inteligencia
                        FROM Personajes
                        WHERE id = %s
                        """,
                        (id_personaje,)
                    )

                    personaje = cursor.fetchone()

                    if personaje is None:
                        return {
                            "ok": False,
                            "mensaje": f"No existe ningún personaje con id {id_personaje}."
                        }

                    (
                        id_db,
                        nombre,
                        nivel,
                        exp,
                        vida_max,
                        vida_actual,
                        mana_max,
                        mana_actual,
                        fuerza,
                        agilidad,
                        inteligencia
                    ) = personaje

                    nivel_inicial = nivel
                    exp_necesaria = nivel * 1000

                    if exp < exp_necesaria:
                        return {
                            "ok": False,
                            "mensaje": f"{nombre} no tiene experiencia suficiente para subir de nivel.",
                            "personaje": {
                                "id": id_db,
                                "nombre": nombre,
                                "nivel": nivel,
                                "exp": exp,
                                "exp_necesaria": exp_necesaria
                            }
                        }

                    niveles_subidos = 0

                    while exp >= exp_necesaria:
                        exp -= exp_necesaria
                        nivel += 1
                        niveles_subidos += 1

                        vida_max += 20
                        mana_max += 10
                        fuerza += 2
                        agilidad += 1
                        inteligencia += 1

                        exp_necesaria = nivel * 1000

                    vida_actual = vida_max
                    mana_actual = mana_max

                    cursor.execute(
                        """
                        UPDATE Personajes
                        SET nivel        = %s,
                            exp          = %s,
                            vida_max     = %s,
                            vida_actual  = %s,
                            mana_max     = %s,
                            mana_actual  = %s,
                            fuerza       = %s,
                            agilidad     = %s,
                            inteligencia = %s
                        WHERE id = %s
                        """,
                        (
                            nivel,
                            exp,
                            vida_max,
                            vida_actual,
                            mana_max,
                            mana_actual,
                            fuerza,
                            agilidad,
                            inteligencia,
                            id_personaje
                        )
                    )

                    conexion.commit()

                    return {
                        "ok": True,
                        "mensaje": f"🎉 {nombre} subió {niveles_subidos} nivel(es): {nivel_inicial} → {nivel}",
                        "personaje": {
                            "id": id_db,
                            "nombre": nombre,
                            "nivel_anterior": nivel_inicial,
                            "nivel_actual": nivel,
                            "niveles_subidos": niveles_subidos,
                            "exp_restante": exp,
                            "exp_para_siguiente_nivel": exp_necesaria,
                            "vida_max": vida_max,
                            "vida_actual": vida_actual,
                            "mana_max": mana_max,
                            "mana_actual": mana_actual,
                            "fuerza": fuerza,
                            "agilidad": agilidad,
                            "inteligencia": inteligencia
                        }
                    }

            except Exception as e:
                conexion.rollback()
                print(f"❌ Error al subir de nivel al personaje {id_personaje}: {e}")

                return {
                    "ok": False,
                    "mensaje": f"Error al subir de nivel al personaje {id_personaje}.",
                    "error": str(e)
                }

    @staticmethod
    def subir_nivel_habilidad(get_db_connection, id_personaje, id_habilidad):
        """
        Sube de nivel una habilidad de un personaje.

        Reglas:
        - El personaje debe existir.
        - La habilidad debe existir.
        - La habilidad debe pertenecer a la clase del personaje o ser genérica.
        - La habilidad no puede superar su nivel máximo.
        - Si la habilidad tiene requisitos, el personaje debe cumplirlos.
        - Si el personaje no tiene la habilidad, se desbloquea en nivel 1.
        - Si ya la tiene, sube 1 nivel.
        """
        with get_db_connection() as conexion:
            if conexion is None:
                return {
                    "ok": False,
                    "mensaje": "No se pudo conectar con la base de datos."
                }

            try:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, nombre, id_clase
                        FROM Personajes
                        WHERE id = %s
                        """,
                        (id_personaje,)
                    )
                    personaje = cursor.fetchone()

                    if personaje is None:
                        return {
                            "ok": False,
                            "mensaje": f"No existe ningún personaje con id {id_personaje}."
                        }

                    id_personaje_db, nombre_personaje, id_clase_personaje = personaje

                    cursor.execute(
                        """
                        SELECT id, nombre, nivel_maximo, id_clase
                        FROM Habilidades
                        WHERE id = %s
                        """,
                        (id_habilidad,)
                    )
                    habilidad = cursor.fetchone()

                    if habilidad is None:
                        return {
                            "ok": False,
                            "mensaje": f"No existe ninguna habilidad con id {id_habilidad}."
                        }

                    id_habilidad_db, nombre_habilidad, nivel_maximo, id_clase_habilidad = habilidad

                    if id_clase_habilidad is not None and id_clase_habilidad != id_clase_personaje:
                        return {
                            "ok": False,
                            "mensaje": f"{nombre_personaje} no puede aprender {nombre_habilidad} porque no pertenece a su clase."
                        }

                    cursor.execute(
                        """
                        SELECT nivel_actual
                        FROM Personajes_Habilidades
                        WHERE id_personaje = %s
                          AND id_habilidad = %s
                        """,
                        (id_personaje, id_habilidad)
                    )
                    habilidad_personaje = cursor.fetchone()

                    nivel_actual = habilidad_personaje[0] if habilidad_personaje else 0

                    if nivel_actual >= nivel_maximo:
                        return {
                            "ok": False,
                            "mensaje": f"{nombre_habilidad} ya está al nivel máximo.",
                            "habilidad": {
                                "id": id_habilidad_db,
                                "nombre": nombre_habilidad,
                                "nivel_actual": nivel_actual,
                                "nivel_maximo": nivel_maximo
                            }
                        }

                    cursor.execute(
                        """
                        SELECT hr.id_requisito,
                               h.nombre,
                               hr.nivel_requisito_necesario,
                               COALESCE(ph.nivel_actual, 0) AS nivel_actual_personaje
                        FROM Habilidades_Requisitos hr
                                 INNER JOIN Habilidades h ON hr.id_requisito = h.id
                                 LEFT JOIN Personajes_Habilidades ph
                                           ON ph.id_habilidad = hr.id_requisito
                                               AND ph.id_personaje = %s
                        WHERE hr.id_habilidad = %s
                        """,
                        (id_personaje, id_habilidad)
                    )
                    requisitos = cursor.fetchall()

                    requisitos_faltantes = []

                    for requisito in requisitos:
                        id_requisito, nombre_requisito, nivel_necesario, nivel_actual_requisito = requisito

                        if nivel_actual_requisito < nivel_necesario:
                            requisitos_faltantes.append({
                                "id_requisito": id_requisito,
                                "nombre": nombre_requisito,
                                "nivel_necesario": nivel_necesario,
                                "nivel_actual": nivel_actual_requisito
                            })

                    if requisitos_faltantes:
                        return {
                            "ok": False,
                            "mensaje": f"{nombre_personaje} no cumple los requisitos para mejorar {nombre_habilidad}.",
                            "requisitos_faltantes": requisitos_faltantes
                        }

                    nuevo_nivel = nivel_actual + 1

                    if habilidad_personaje is None:
                        cursor.execute(
                            """
                            INSERT INTO Personajes_Habilidades
                                (id_personaje, id_habilidad, nivel_actual, exp_habilidad)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (id_personaje, id_habilidad, nuevo_nivel, 0)
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE Personajes_Habilidades
                            SET nivel_actual = %s
                            WHERE id_personaje = %s
                              AND id_habilidad = %s
                            """,
                            (nuevo_nivel, id_personaje, id_habilidad)
                        )

                    conexion.commit()

                    return {
                        "ok": True,
                        "mensaje": f"✨ {nombre_personaje} mejoró {nombre_habilidad}: nivel {nivel_actual} → {nuevo_nivel}",
                        "habilidad": {
                            "id": id_habilidad_db,
                            "nombre": nombre_habilidad,
                            "nivel_anterior": nivel_actual,
                            "nivel_actual": nuevo_nivel,
                            "nivel_maximo": nivel_maximo
                        }
                    }

            except Exception as e:
                conexion.rollback()
                print(f"❌ Error al subir nivel de habilidad: {e}")

                return {
                    "ok": False,
                    "mensaje": "Error al subir el nivel de la habilidad.",
                    "error": str(e)
                }