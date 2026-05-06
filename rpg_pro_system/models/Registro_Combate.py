from datetime import datetime

class Registro_Combate:
    def __init__(self, id_personaje, id_enemigo, turno, accion, dano_infligido, dano_received, resultado, fecha=None, id=None):
        self.id = id
        self.id_personaje = id_personaje
        self.id_enemigo = id_enemigo
        self.turno = turno
        self.accion = accion
        self.dano_infligido = dano_infligido
        self.dano_received = dano_received
        self.resultado = resultado
        self.fecha = fecha or datetime.now()

    @classmethod
    def registrar_turno(get_db_connection, registro):
        """
        Guarda un nuevo movimiento de combate en la base de datos.
        """
        with get_db_connection() as conexion:
            if conexion is None: return False
            try:
                with conexion.cursor() as cursor:
                    query = """
                        INSERT INTO Registros_Combate 
                        (id_personaje, id_enemigo, turno, accion, dano_infligido, dano_received, resultado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, (
                        registro.id_personaje, registro.id_enemigo, registro.turno,
                        registro.accion, registro.dano_infligido, registro.dano_received,
                        registro.resultado
                    ))
                conexion.commit()
                return True
            except Exception as e:
                print(f"❌ Error al guardar registro de combate: {e}")
                return False

    @classmethod
    def obtener_historial_personaje(get_db_connection, personaje_id):
        """
        Recupera todos los combates de un personaje, incluyendo el nombre del enemigo.
        """
        historial = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    query = """
                        SELECT rc.*, e.nombre as nombre_enemigo
                        FROM Registros_Combate rc
                        LEFT JOIN Enemigos e ON rc.id_enemigo = e.id
                        WHERE rc.id_personaje = %s
                        ORDER BY rc.fecha DESC, rc.turno ASC
                    """
                    cursor.execute(query, (personaje_id,))
                    filas = cursor.fetchall()

                    for f in filas:
                        # f[0]=id, f[1]=id_p, f[2]=id_e, f[3]=turno, f[4]=accion, 
                        # f[5]=dano_i, f[6]=dano_r, f[7]=resultado, f[8]=fecha, f[9]=nombre_e
                        historial.append({
                            "id": f[0],
                            "turno": f[3],
                            "accion": f[4],
                            "dano_hecho": f[5],
                            "dano_recibido": f[6],
                            "resultado": f[7],
                            "fecha": f[8].strftime("%Y-%m-%d %H:%M"),
                            "enemigo": f[9] if f[9] else "Desconocido"
                        })
            except Exception as e:
                print(f"❌ Error al obtener historial: {e}")
        return historial