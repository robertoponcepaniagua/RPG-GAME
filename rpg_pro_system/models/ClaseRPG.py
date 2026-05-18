class ClaseRPG:
    def __init__(self, nombre, descripcion, factor_dano=1.0, dado_vida=8, recurso_primario='Mana'):
        self.nombre = nombre
        self.descripcion = descripcion
        self.factor_dano = float(factor_dano)
        self.dado_vida = dado_vida
        self.recurso_primario = recurso_primario