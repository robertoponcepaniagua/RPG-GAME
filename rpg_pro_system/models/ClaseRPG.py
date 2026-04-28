class ClaseRPG:
    def __init__(self, nombre, descripcion, factor_dano=1.0, dado_vida=8, recurso_primario='Mana'):
        self.nombre = nombre
        self.descripcion = descripcion
        self.factor_dano = float(factor_dano)
        self.dado_vida = dado_vida
        self.recurso_primario = recurso_primario

        # --- Atributos de Estado ---
        self.vida_max = 0
        self.vida_actual = 0
        self.mana_max = 0
        self.mana_actual = 0
        self.fuerza = 10
        self.agilidad = 10
        self.inteligencia = 10
        self.nivel = 1 #

    def calcular_ataque_basico(self):
        # Daño basado en fuerza multiplicado por el factor de la clase
        return self.fuerza * self.factor_dano

    def __str__(self):
        return f"{self.nombre} (Nivel {self.nivel})"