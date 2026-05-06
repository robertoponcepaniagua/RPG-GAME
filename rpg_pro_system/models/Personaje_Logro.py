"""CREATE TABLE Personajes_Logros (
    id_personaje    INT REFERENCES Personajes(id) ON DELETE CASCADE,
    id_logro        INT REFERENCES Logros(id) ON DELETE CASCADE,
    desbloqueado_en TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id_personaje, id_logro)
);"""

class Personaje_Logro:
    def __init__(self, id_personaje, id_logro, desbloqueado_en):
        self.id_personaje = id_personaje
        self.id_logro = id_logro
        self.desbloqueado_en = desbloqueado_en

    @classmethod
    def obtener_logros_desbloqueados(get_db_connection, personaje_id):
        """
        Obtiene la lista de logros que un personaje específico ha conseguido.
        """
        logros_conseguidos = []

        with get_db_connection() as conexion:
            if conexion is None:
                return []

            try:
                with conexion.cursor() as cursor:
                    # Hacemos JOIN para traer los detalles del logro (nombre, icono, etc.)
                    query = """
                            SELECT pl.id_personaje, \
                                   pl.id_logro, \
                                   pl.desbloqueado_en,
                                   l.nombre, \
                                   l.descripcion, \
                                   l.icono
                            FROM Personajes_Logros pl
                                     JOIN Logros l ON pl.id_logro = l.id
                            WHERE pl.id_personaje = %s
                            ORDER BY pl.desbloqueado_en DESC \
                            """
                    cursor.execute(query, (personaje_id,))
                    filas = cursor.fetchall()

                    for fila in filas:
                        p_id, l_id, fecha, nombre, desc, icono = fila

                        # Creamos el objeto con tu constructor
                        logro_p = Personaje_Logro(p_id, l_id, fecha)

                        # Añadimos la info extra para el frontend
                        logros_conseguidos.append({
                            "id_logro": logro_p.id_logro,
                            "nombre": nombre,
                            "descripcion": desc,
                            "icono": icono,
                            "desbloqueado_en": logro_p.desbloqueado_en.strftime(
                                "%Y-%m-%d %H:%M:%S") if logro_p.desbloqueado_en else None
                        })

                    print(f"🏅 Logros recuperados para el personaje {personaje_id}: {len(logros_conseguidos)}")
            except Exception as e:
                print(f"❌ Error al obtener logros del personaje: {e}")

        return logros_conseguidos