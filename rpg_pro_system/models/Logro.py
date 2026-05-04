class Logro:
    def __init__(self, id, nombre, descripcion, icono, condicion):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.icono = icono
        self.condicion = condicion

    @staticmethod
    def obtener_logros(get_db_connection):
        """
        Recupera el listado completo de logros disponibles en el sistema.
        """
        logros_data = []

        with get_db_connection() as conexion:
            if conexion is None:
                return []

            try:
                with conexion.cursor() as cursor:
                    # En los logros no solemos filtrar tanto, pero traemos todo
                    query = "SELECT id, nombre, descripcion, icono, condicion FROM Logros"
                    cursor.execute(query)
                    filas = cursor.fetchall()

                    for fila in filas:
                        # Desempaquetado claro
                        id_logro, nom, desc, ico, cond = fila

                        # Instanciamos usando tu constructor
                        logro_obj = Logro(id_logro, nom, desc, ico, cond)

                        # Formateamos para el JSON
                        logros_data.append({
                            "id": logro_obj.id,
                            "nombre": logro_obj.nombre,
                            "descripcion": logro_obj.descripcion,
                            "icono": logro_obj.icono,
                            "condicion": logro_obj.condicion
                        })

                    print(f"🏆 Logros cargados: {len(logros_data)} registros.")
            except Exception as e:
                print(f"❌ Error al consultar logros: {e}")

        return logros_data