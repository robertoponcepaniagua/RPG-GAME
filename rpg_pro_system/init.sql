CREATE TABLE Razas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50),
    mod_vida INT,
    mod_fuerza INT
);

CREATE TABLE Clases_RPG (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50),
    descripcion TEXT
);

CREATE TABLE Personajes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50),
    nivel INT DEFAULT 1,
    exp INT DEFAULT 0,
    oro INT DEFAULT 100,
    vida_actual INT,
    id_raza INT REFERENCES Razas(id),
    id_clase INT REFERENCES Clases_RPG(id)
);

CREATE TABLE Habilidades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50),
    nivel_maximo INT DEFAULT 5,
    id_clase INT REFERENCES Clases_RPG(id)
);

-- Tabla de Dependencias (Árbol de Habilidades)
CREATE TABLE Habilidades_Requisitos (
    id_habilidad INT REFERENCES Habilidades(id),
    id_requisito INT REFERENCES Habilidades(id),
    nivel_requisito_necesario INT DEFAULT 1,
    PRIMARY KEY (id_habilidad, id_requisito)
);

-- Progreso Real del Jugador
CREATE TABLE Personajes_Habilidades (
    id_personaje INT REFERENCES Personajes(id),
    id_habilidad INT REFERENCES Habilidades(id),
    nivel_actual INT DEFAULT 0, -- 0 significa bloqueada
    PRIMARY KEY (id_personaje, id_habilidad)
);

-- Datos de Ejemplo
INSERT INTO Razas (nombre, mod_vida, mod_fuerza) VALUES ('Humano', 100, 10), ('Elfo', 80, 8);
INSERT INTO Clases_RPG (nombre, descripcion) VALUES ('Guerrero', 'Especialista en combate físico'), ('Mago', 'Maestro de las artes arcanas');
INSERT INTO Habilidades (nombre, nivel_maximo, id_clase) VALUES 
('Corte', 5, 1), ('Torbellino', 5, 1), ('Bola de Fuego', 5, 2);
-- Requisito: Torbellino requiere Corte al nivel 3
INSERT INTO Habilidades_Requisitos (id_habilidad, id_requisito, nivel_requisito_necesario) VALUES (2, 1, 3);
INSERT INTO Personajes (nombre, nivel, vida_actual, id_raza, id_clase) VALUES ('Aragorn', 1, 110, 1, 1);