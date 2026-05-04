class Habilidad_Requisitos:
    def __init__(self, id_habilidad, id_requisito, nivel_requisito_necesario):
        self.id_habilidad = id_habilidad
        self.id_requisito = id_requisito
        self.nivel_requisito_necesario = nivel_requisito_necesario

    @staticmethod
    def obtener_requisitos_de_habilidad(get_db_connection, habilidad_id):
        """
        Devuelve la lista de habilidades que necesitas tener para aprender una específica.
        """
        requisitos = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    # JOIN con la tabla Habilidades para saber el NOMBRE del requisito
                    query = """
                        SELECT hr.id_requisito, h.nombre, hr.nivel_requisito_necesario
                        FROM Habilidades_Requisitos hr
                        JOIN Habilidades h ON hr.id_requisito = h.id
                        WHERE hr.id_habilidad = %s
                    """
                    cursor.execute(query, (habilidad_id,))
                    filas = cursor.fetchall()

                    for fila in filas:
                        id_req, nombre_req, nivel_req = fila
                        requisitos.append({
                            "id_requisito": id_req,
                            "nombre_habilidad_previa": nombre_req,
                            "nivel_necesario": nivel_req
                        })
            except Exception as e:
                print(f"❌ Error al consultar requisitos: {e}")
        return requisitos