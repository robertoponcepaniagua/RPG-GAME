from rpg_pro_system.models import ClaseRPG


class Guerrero(ClaseRPG):
    def __init__(self):
        super().__init__(nombre="Guerrero", descripcion="Maestro del combate físico, escudo y espada.", factor_dano=1.40, dado_vida=10, recurso_primario='Rabia')

    def calcular_ataque_basico(self):
        return self.nivel * self.factor_dano