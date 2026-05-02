from models.ClaseRPG import ClaseRPG

class Guerrero(ClaseRPG):
    def __init__(self):
        super().__init__(nombre="Guerrero", descripcion="Maestro del combate físico, escudo y espada.", factor_dano=1.40, dado_vida=10, recurso_primario='Rabia')

    def calcular_ataque_basico(self):
        return self.nivel * self.factor_dano

    @staticmethod
    def obtener_guerreros(get_db_connection):
        """
        Recupera solo los personajes que pertenecen a la clase Guerrero
        e instancia objetos de la clase específica.
        """
        guerreros_data = []

        with get_db_connection() as conexion:
            if conexion is None:
                return []

            try:
                with conexion.cursor() as cursor:
                    # 1. Filtramos por el ID de la clase Guerrero
                    # También añadimos vida_max que es necesaria para la lógica de Guerrero
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
                            WHERE c.nombre = 'Guerrero' \
                            """
                    cursor.execute(query)
                    filas = cursor.fetchall()

                    for fila in filas:
                        id_db, nombre, nivel, exp, oro, vida, vida_max, raza, clase = fila

                        # 2. Instanciamos la clase específica Guerrero
                        # Nota: Asegúrate de que tu clase Guerrero acepte estos parámetros o
                        # use un método para cargar los datos base.
                        p = Guerrero()
                        p.id = id_db
                        p.nombre = nombre
                        p.nivel = nivel
                        p.exp = exp
                        p.oro = oro
                        p.vida_actual = vida
                        p.vida_max = vida_max
                        p.id_raza = raza
                        p.id_clase = clase

                        # 3. Convertimos a diccionario incluyendo el cálculo de ataque único del Guerrero
                        guerreros_data.append({
                            "id": p.id,
                            "nombre": p.nombre,
                            "nivel": p.nivel,
                            "oro": p.oro,
                            "vida_actual": p.vida_actual,
                            "vida_max": p.vida_max,
                            "ataque_basico": p.calcular_ataque_basico(),  # Lógica específica de Guerrero
                            "recurso": p.recurso_primario  # 'Rabia'
                        })

                    print(f"✅ Guerreros recuperados: {len(guerreros_data)}")
            except Exception as e:
                print(f"❌ Error al consultar guerreros: {e}")

        return guerreros_data