class ClaseRPG:
    def __init__(self, nombre, vida, mana, fuerza, agilidad, inteligencia):
        self.nombre = nombre
        self._vida = vida
        self._mana = mana
        self._fuerza = fuerza
        self._agilidad = agilidad
        self._inteligencia = inteligencia
        self.nivel = 1
        self.factor_dano = 1.0
        self.dado_vida = 8
        self.recurso_primario = "Mana"


    # METODO ATACAR: