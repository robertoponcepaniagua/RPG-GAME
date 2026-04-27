class Raza:
    def __init__(self, nombre, vida_extra, fuerza):
        self.nombre = nombre
        self.vida_extra = vida_extra
        self.fuerza = fuerza

class ClaseRPG:
    def __init__(self, nombre, skill_principal):
        self.nombre = nombre
        self.skill_principal = skill_principal

class Guerrero(ClaseRPG):
    def __init__(self):
        super().__init__("Guerrero", "Ataque Físico")
        self.multiplicador_daño = 1.5

class Mago(ClaseRPG):
    def __init__(self):
        super().__init__("Mago", "Hechizo")
        self.multiplicador_magico = 2.0

class Personaje:
    def __init__(self, db_data, raza_obj, clase_obj):
        self.id = db_data[0]
        self.nombre = db_data[1]
        self.nivel = db_data[2]
        self.vida = db_data[5]
        self.raza = raza_obj
        self.clase = clase_obj