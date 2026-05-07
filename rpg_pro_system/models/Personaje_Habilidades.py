"""
    id_personaje    INT REFERENCES Personajes(id) ON DELETE CASCADE,
    id_habilidad    INT REFERENCES Habilidades(id) ON DELETE CASCADE,
    nivel_actual    INT DEFAULT 0,
    exp_habilidad   INT DEFAULT 0,
    PRIMARY KEY (id_personaje, id_habilidad)
"""
class Personaje_Habilidades:
    def __init__(self, id_personaje, id_habilidad, nivel_actual, exp_habilidad):
        self.id_personaje = id_personaje
        self.id_habilidad = id_habilidad
        self.nivel_actual = nivel_actual
        self.exp_habilidad = exp_habilidad
        