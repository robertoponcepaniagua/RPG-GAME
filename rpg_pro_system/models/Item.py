class Item:
    def __init__(self, id, nombre, descripcion, precio, tipo, mod_vida, mod_mana, mod_fuerza, mod_agilidad, mod_inteligencia, dano_bonus, rareza):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.tipo = tipo
        self.mod_vida = mod_vida
        self.mod_mana = mod_mana
        self.mod_fuerza = mod_fuerza
        self.mod_agilidad = mod_agilidad
        self.mod_inteligencia = mod_inteligencia
        self.dano_bonus = dano_bonus
        self.rareza = rareza

    @staticmethod
    def obtener_items(get_db_connection, tipo=None, rareza=None):
        items_data = []

        with get_db_connection() as conexion:
            if conexion is None: return []

            try:
                with conexion.cursor() as cursor:
                    query = "SELECT * FROM Items"
                    filtros = []
                    valores = []

                    if tipo:
                        filtros.append("tipo = %s")
                        valores.append(tipo)
                    if rareza:
                        filtros.append("rareza = %s")
                        valores.append(rareza)

                    if filtros:
                        query += " WHERE " + " AND ".join(filtros)

                    cursor.execute(query, tuple(valores))
                    filas = cursor.fetchall()

                    for fila in filas:
                        # 1. Desempaquetado
                        (id_item, nombre, desc, precio, tipo_item, mod_v,
                         mod_m, mod_f, mod_a, mod_i, dano, rareza_item) = fila

                        # 2. Instanciamos el objeto
                        it = Item(id_item, nombre, desc, precio, tipo_item, mod_v,
                                  mod_m, mod_f, mod_a, mod_i, dano, rareza_item)

                        # 3. Construimos el diccionario usando los atributos del objeto 'it'
                        items_data.append({
                            "id": it.id,
                            "nombre": it.nombre,
                            "descripcion": it.descripcion,
                            "precio": it.precio,
                            "tipo": it.tipo,
                            "stats": {
                                "vida": it.mod_vida,
                                "mana": it.mod_mana,
                                "fuerza": it.mod_fuerza,
                                "agilidad": it.mod_agilidad,
                                "inteligencia": it.mod_inteligencia,
                                "dano_extra": it.dano_bonus
                            },
                            "rareza": it.rareza
                        })

                    print(f"✅ Catálogo de items cargado: {len(items_data)} registros.")
            except Exception as e:
                print(f"❌ Error al consultar catálogo de items: {e}")

        return items_data