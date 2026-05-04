class Raza:
    def __init__(self, id, nombre, descripcion, mod_vida, mod_mana, mod_fuerza, mod_agilidad, mod_inteligencia, habilidad_racial):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.mod_vida = mod_vida
        self.mod_mana = mod_mana
        self.mod_fuerza = mod_fuerza
        self.mod_agilidad = mod_agilidad
        self.mod_inteligencia = mod_inteligencia
        self.habilidad_racial = habilidad_racial

    @staticmethod
    def obtener_razas(get_db_connection):
        """
        Obtiene el listado de todas las razas disponibles y sus bonificadores.
        """
        razas_data = []
        with get_db_connection() as conexion:
            if conexion is None: return []
            try:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT * FROM Razas")
                    filas = cursor.fetchall()

                    for fila in filas:
                        # Desempaquetado de las 9 columnas
                        (r_id, nom, desc, m_v, m_m, m_f, m_a, m_i, hab) = fila
                        
                        # Instancia
                        raza_obj = Raza(r_id, nom, desc, m_v, m_m, m_f, m_a, m_i, hab)

                        # Formato JSON
                        razas_data.append({
                            "id": raza_obj.id,
                            "nombre": raza_obj.nombre,
                            "descripcion": raza_obj.descripcion,
                            "stats_base": {
                                "vida": raza_obj.mod_vida,
                                "mana": raza_obj.mod_mana,
                                "fuerza": raza_obj.mod_fuerza,
                                "agilidad": raza_obj.mod_agilidad,
                                "inteligencia": raza_obj.mod_inteligencia
                            },
                            "habilidad_racial": raza_obj.habilidad_racial
                        })
            except Exception as e:
                print(f"❌ Error al consultar razas: {e}")
        return razas_data