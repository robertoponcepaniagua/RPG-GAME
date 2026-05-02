from models.ClaseRPG import ClaseRPG

class Mago(ClaseRPG):
    def __init__(self):
        super().__init__(nombre="Mago", descripcion="Canalizador de energías arcanas destructivas.", factor_dano=1.80, dado_vida=6, recurso_primario='Maná')

    def calcular_ataque_basico(self):
        return self.nivel * self.factor_dano

    @staticmethod
    def obtener_magos(get_db_connection):
        """
        Recupera los personajes de clase Mago e instancia la clase específica.
        """
        magos_data = []

        with get_db_connection() as conexion:
            if conexion is None: return []

            try:
                with conexion.cursor() as cursor:
                    query = """
                            SELECT p.id, \
                                   p.nombre, \
                                   p.nivel, \
                                   p.exp, \
                                   p.oro, \
                                   p.vida_actual, \
                                   p.vida_max, \
                                   p.id_raza, \
                                   p.id_clase
                            FROM personajes p
                                     INNER JOIN clases_rpg c ON p.id_clase = c.id
                            WHERE c.nombre = 'Mago' \
                            """
                    cursor.execute(query)
                    filas = cursor.fetchall()

                    for fila in filas:
                        id_db, nombre, nivel, exp, oro, vida, vida_max, raza, clase = fila

                        # Instanciamos la clase específica Mago
                        m = Mago()
                        m.id, m.nombre, m.nivel = id_db, nombre, nivel
                        m.vida_actual, m.vida_max = vida, vida_max

                        magos_data.append({
                            "id": m.id,
                            "nombre": m.nombre,
                            "nivel": m.nivel,
                            "ataque_magico": round(m.calcular_ataque_basico(), 2),
                            "recurso": m.recurso_primario,  # 'Maná'
                            "vida": f"{m.vida_actual}/{m.vida_max}"
                        })
            except Exception as e:
                print(f"❌ Error al consultar magos: {e}")

        return magos_data