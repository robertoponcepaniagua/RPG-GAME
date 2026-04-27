-- ============================================================
--  RPG PRO SYSTEM — Esquema Relacional Corregido
-- ============================================================

-- 1. Borrado de tablas por orden de dependencia (Evita errores de FK)
DROP TABLE IF EXISTS Personajes_Logros, Logros, Registros_Combate, Enemigos, 
                     Inventarios, Items, Tipos_Item, Personajes_Habilidades, 
                     Habilidades_Requisitos, Habilidades, Personajes, Clases_RPG, Razas;

-- -----------------------------------------------------------
-- TABLAS MAESTRAS
-- -----------------------------------------------------------

CREATE TABLE Razas (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    mod_vida    INT DEFAULT 0,
    mod_mana    INT DEFAULT 0,
    mod_fuerza  INT DEFAULT 0,
    mod_agilidad INT DEFAULT 0,
    mod_inteligencia INT DEFAULT 0,
    habilidad_racial VARCHAR(100)
);

CREATE TABLE Clases_RPG (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE,
    descripcion     TEXT,
    factor_dano     NUMERIC(4,2) DEFAULT 1.0,
    dado_vida       INT DEFAULT 8 CHECK (dado_vida IN (6, 8, 10, 12)),
    recurso_primario VARCHAR(20) DEFAULT 'Mana'
);

CREATE TABLE Personajes (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) NOT NULL,
    nivel       INT DEFAULT 1 CHECK (nivel > 0),
    exp         INT DEFAULT 0,
    oro         INT DEFAULT 100,
    vida_max    INT NOT NULL,
    vida_actual INT NOT NULL,
    mana_max    INT DEFAULT 0,
    mana_actual INT DEFAULT 0,
    fuerza      INT DEFAULT 10,
    agilidad    INT DEFAULT 10,
    inteligencia INT DEFAULT 10,
    id_raza     INT REFERENCES Razas(id) ON DELETE SET NULL,
    id_clase    INT REFERENCES Clases_RPG(id) ON DELETE SET NULL,
    creado_en   TIMESTAMP DEFAULT NOW(),
    -- Garantizamos que la vida actual no supere la máxima
    CONSTRAINT check_vida CHECK (vida_actual <= vida_max)
);

-- -----------------------------------------------------------
-- HABILIDADES
-- -----------------------------------------------------------

CREATE TABLE Habilidades (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(80) NOT NULL,
    descripcion     TEXT,
    tipo            VARCHAR(20) DEFAULT 'activa',
    nivel_maximo    INT DEFAULT 5,
    costo_mana      INT DEFAULT 0,
    dano_base       INT DEFAULT 0,
    id_clase        INT REFERENCES Clases_RPG(id) ON DELETE CASCADE
);

CREATE TABLE Habilidades_Requisitos (
    id_habilidad            INT REFERENCES Habilidades(id) ON DELETE CASCADE,
    id_requisito            INT REFERENCES Habilidades(id) ON DELETE CASCADE,
    nivel_requisito_necesario INT DEFAULT 1,
    PRIMARY KEY (id_habilidad, id_requisito),
    CONSTRAINT no_autorreferencia CHECK (id_habilidad <> id_requisito)
);

CREATE TABLE Personajes_Habilidades (
    id_personaje    INT REFERENCES Personajes(id) ON DELETE CASCADE,
    id_habilidad    INT REFERENCES Habilidades(id) ON DELETE CASCADE,
    nivel_actual    INT DEFAULT 0,
    exp_habilidad   INT DEFAULT 0,
    PRIMARY KEY (id_personaje, id_habilidad)
);

-- -----------------------------------------------------------
-- INVENTARIO
-- -----------------------------------------------------------

CREATE TABLE Tipos_Item (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE Items (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(80) NOT NULL,
    descripcion TEXT,
    precio      INT DEFAULT 10 CHECK (precio >= 0),
    tipo        INT REFERENCES Tipos_Item(id),
    mod_vida    INT DEFAULT 0,
    mod_mana    INT DEFAULT 0,
    mod_fuerza  INT DEFAULT 0,
    mod_agilidad INT DEFAULT 0,
    mod_inteligencia INT DEFAULT 0,
    dano_bonus  INT DEFAULT 0,
    rareza      VARCHAR(20) DEFAULT 'Común'
);

CREATE TABLE Inventarios (
    id              SERIAL PRIMARY KEY,
    id_personaje    INT REFERENCES Personajes(id) ON DELETE CASCADE,
    id_item         INT REFERENCES Items(id) ON DELETE CASCADE,
    cantidad        INT DEFAULT 1 CHECK (cantidad > 0),
    equipado        BOOLEAN DEFAULT FALSE,
    UNIQUE (id_personaje, id_item)
);

-- -----------------------------------------------------------
-- COMBATE Y LOGROS (Estructura idéntica, corregida integridad)
-- -----------------------------------------------------------

CREATE TABLE Enemigos (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(60) NOT NULL,
    nivel       INT DEFAULT 1,
    vida_max    INT NOT NULL,
    dano_base   INT DEFAULT 5,
    exp_recom   INT DEFAULT 20,
    oro_recom   INT DEFAULT 10,
    descripcion TEXT
);

CREATE TABLE Registros_Combate (
    id              SERIAL PRIMARY KEY,
    id_personaje    INT REFERENCES Personajes(id) ON DELETE SET NULL,
    id_enemigo      INT REFERENCES Enemigos(id) ON DELETE SET NULL,
    turno           INT DEFAULT 1,
    accion          VARCHAR(100),
    dano_infligido  INT DEFAULT 0,
    dano_received   INT DEFAULT 0,
    resultado       VARCHAR(20),
    fecha           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE Logros (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(80) NOT NULL,
    descripcion TEXT,
    icono       VARCHAR(10) DEFAULT '🏆',
    condicion   VARCHAR(100)
);

CREATE TABLE Personajes_Logros (
    id_personaje    INT REFERENCES Personajes(id) ON DELETE CASCADE,
    id_logro        INT REFERENCES Logros(id) ON DELETE CASCADE,
    desbloqueado_en TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id_personaje, id_logro)
);

-- ============================================================
--  DATOS SEMILLA
-- ============================================================

-- Razas
INSERT INTO Razas (nombre, descripcion, mod_vida, mod_mana, mod_fuerza, mod_agilidad, mod_inteligencia, habilidad_racial) VALUES
('Humano',    'Versátiles y adaptables, dominan todas las artes.',          100,  50, 10, 10, 10, 'Determinación: +10% EXP'),
('Elfo',      'Gracia inmortal y afinidad arcana incomparable.',             80, 120,  6, 14, 14, 'Visión Élfica: nunca fallan en la oscuridad'),
('Enano',     'Forjados en la roca, resistencia sobrehumana.',              140,  30, 14,  8,  8, 'Resiliencia: -15% daño recibido'),
('Semiorco',  'Fuerza bruta y un instinto de supervivencia sin igual.',     130,  20, 16,  9,  7, 'Resistencia Imparable: sobrevive con 1 HP una vez/día'),
('Gnomo',     'Inventores ingeniosos con un talento arcano innato.',         70, 100,  6, 12, 16, 'Ilusión Menor: confunde al enemigo cada 3 turnos'),
('Semielfo',  'Heredan lo mejor de dos mundos, equilibrio perfecto.',        90,  90, 10, 12, 12, 'Adaptabilidad: +1 habilidad de otra clase'),
('Tiefling',  'Descendientes de pactos infernales, poder oscuro en sus venas.',  85, 110,  9, 11, 13, 'Herencia Infernal: resistencia al fuego'),
('Dracónido', 'Linaje dracónico que otorga un aliento elemental devastador.', 120,  60, 14, 10, 10, 'Aliento Dracónico: daño en área cada 5 turnos');

-- Clases
INSERT INTO Clases_RPG (nombre, descripcion, factor_dano, dado_vida, recurso_primario) VALUES
('Guerrero',  'Maestro del combate físico, escudo y espada.',    1.40, 10, 'Rabia'),
('Mago',      'Canalizador de energías arcanas destructivas.',   1.80,  6, 'Maná'),
('Pícaro',    'Experto en ataques furtivos y venenos letales.',  1.60,  8, 'Energía'),
('Paladín',   'Guerrero sagrado que cura y protege.',            1.30, 10, 'Fe'),
('Druida',    'Guardián de la naturaleza con magia primigenia.', 1.50,  8, 'Maná'),
('Bárbaro',   'Fuerza bruta desatada, combate en frenesí.',      1.70, 12, 'Rabia'),
('Clérigo',   'Sanador y escudo divino de su grupo.',            1.10, 8,  'Fe'),
('Ranger',    'Arquero certero y rastreador en cualquier terreno.', 1.50, 10, 'Energía'),
('Bardo',     'Músico mágico que inspira a aliados y engaña enemigos.', 1.20, 8, 'Inspiración'),
('Brujo',     'Vinculado a entidades oscuras, poder a un alto precio.', 1.70, 8, 'Maná'),
('Hechicero', 'Magia innata que fluye sin control desde su interior.', 1.90, 6, 'Maná'),
('Monje',     'Artes marciales y ki interior como armas perfectas.', 1.45, 8, 'Ki');

-- Habilidades — Guerrero (id_clase=1)
INSERT INTO Habilidades (nombre, descripcion, tipo, nivel_maximo, costo_mana, dano_base, id_clase) VALUES
('Corte Básico',    'Un golpe directo con la espada.',                            'activa',  5,  0, 10, 1),
('Escudo Alzado',   'Adopta postura defensiva, reduce daño recibido.',            'activa',  5,  0,  0, 1),
('Torbellino',      'Gira atacando a todos los enemigos cercanos.',               'activa',  5,  5, 18, 1),
('Golpe Aplastante','Golpe que puede aturdír al objetivo un turno.',              'activa',  5, 10, 22, 1),
('Grito de Guerra', 'Aumenta el daño del grupo durante 3 turnos.',               'activa',  3, 15,  0, 1),
('Maestría Marcial','Pasiva: +2% daño por nivel de esta habilidad.',             'pasiva',  5,  0,  5, 1),
('Filo Imparable',  'ULTIMATE: Ataque devastador que ignora la armadura enemiga.','ultimate',1, 30, 60, 1);

-- Habilidades — Mago (id_clase=2)
INSERT INTO Habilidades (nombre, descripcion, tipo, nivel_maximo, costo_mana, dano_base, id_clase) VALUES
('Misil Mágico',    'Proyectil de energía pura e infalible.',                    'activa',  5, 5, 12, 2),
('Escudo Arcano',   'Barrera mágica que absorbe daño.',                          'activa',  5, 8,  0, 2),
('Bola de Fuego',   'Explosión ardiente de radio amplio.',                       'activa',  5,15, 30, 2),
('Rayo de Hielo',   'Congela al objetivo, reduciendo su velocidad.',             'activa',  5,12, 20, 2),
('Teletransporte',  'Se desplaza instantáneamente a una posición.',              'activa',  3,20,  0, 2),
('Erudición Arcana','Pasiva: reduce el costo de maná en 5% por nivel.',         'pasiva',  5, 0,  0, 2),
('Nova Arcana',     'ULTIMATE: Libera toda la energía en una explosión masiva.',  'ultimate',1,50, 80, 2);

-- Habilidades — Pícaro (id_clase=3)
INSERT INTO Habilidades (nombre, descripcion, tipo, nivel_maximo, costo_mana, dano_base, id_clase) VALUES
('Puñalada Trapera','Ataque por la espalda con daño crítico.',                  'activa',  5, 5, 15, 3),
('Veneno',          'Envena al objetivo causando daño continuo.',               'activa',  5, 8, 8,  3),
('Invisibilidad',   'Se oculta durante 2 turnos.',                              'activa',  3,12,  0, 3),
('Evasión',         'Pasiva: % de esquivar ataques por nivel.',                 'pasiva',  5, 0,  0, 3),
('Golpe Mortal',    'ULTIMATE: Combo letal de 5 golpes rápidos.',               'ultimate',1,30, 55, 3);

-- Habilidades — Paladín (id_clase=4)
INSERT INTO Habilidades (nombre, descripcion, tipo, nivel_maximo, costo_mana, dano_base, id_clase) VALUES
('Golpe Divino',    'Ataque imbuido de luz sagrada.',                           'activa',  5, 8, 14, 4),
('Curación Menor',  'Restaura puntos de vida al personaje.',                    'activa',  5,10,  0, 4),
('Aura de Luz',     'Pasiva: regenera vida a aliados cada turno.',              'pasiva',  5, 0,  0, 4),
('Smite Sagrado',   'ULTIMATE: Condena divina de daño masivo.',                 'ultimate',1,35, 65, 4);

-- Habilidades genéricas (sin clase) — id_clase NULL
INSERT INTO Habilidades (nombre, descripcion, tipo, nivel_maximo, costo_mana, dano_base, id_clase) VALUES
('Meditación',      'Recupera maná/energía sin combate.',                       'activa',  3, 0,  0, NULL),
('Primer Auxilio',  'Cura básica de emergencia.',                               'activa',  3, 5,  0, NULL);


-- Borramos datos previos para evitar duplicados si re-ejecutas
DELETE FROM Habilidades_Requisitos;

-- Insertar requisitos buscando los IDs por nombre
-- Formato: (id_habilidad, id_requisito, nivel_necesario)

-- Torbellino requiere Corte Básico lv3
INSERT INTO Habilidades_Requisitos (id_habilidad, id_requisito, nivel_requisito_necesario)
VALUES (
    (SELECT id FROM Habilidades WHERE nombre = 'Torbellino'),
    (SELECT id FROM Habilidades WHERE nombre = 'Corte Básico'),
    3
);

-- Nova Arcana requiere Bola de Fuego lv4
INSERT INTO Habilidades_Requisitos (id_habilidad, id_requisito, nivel_requisito_necesario)
VALUES (
    (SELECT id FROM Habilidades WHERE nombre = 'Nova Arcana'),
    (SELECT id FROM Habilidades WHERE nombre = 'Bola de Fuego'),
    4
);

-- Nova Arcana requiere también Rayo de Hielo lv3
INSERT INTO Habilidades_Requisitos (id_habilidad, id_requisito, nivel_requisito_necesario)
VALUES (
    (SELECT id FROM Habilidades WHERE nombre = 'Nova Arcana'),
    (SELECT id FROM Habilidades WHERE nombre = 'Rayo de Hielo'),
    3
);

-- Smite Sagrado requiere Aura de Luz lv3 (El que te daba error)
INSERT INTO Habilidades_Requisitos (id_habilidad, id_requisito, nivel_requisito_necesario)
VALUES (
    (SELECT id FROM Habilidades WHERE nombre = 'Smite Sagrado'),
    (SELECT id FROM Habilidades WHERE nombre = 'Aura de Luz'),
    3
);
-- Tipos de ítem
INSERT INTO Tipos_Item (nombre) VALUES ('Arma'), ('Armadura'), ('Consumible'), ('Accesorio'), ('Escudo');

-- Items
INSERT INTO Items (nombre, descripcion, precio, tipo, mod_vida, mod_fuerza, mod_inteligencia, dano_bonus, rareza) VALUES
('Espada Corta',         'Hoja estándar de inicio.',                              50, 1,  0, 2,  0,  8, 'Común'),
('Hacha de Batalla',     'Arma pesada con alto daño.',                           120, 1,  0, 4,  0, 15, 'Raro'),
('Báculo Arcano',        'Amplifica el poder mágico.',                           100, 1,  0, 0,  5, 10, 'Raro'),
('Daga Envenenada',      'Aplica veneno en cada golpe.',                         140, 1,  0, 1,  0, 12, 'Épico'),
('Mazo Sagrado',         'Arma bendita del paladín.',                            130, 1,  0, 3,  2, 12, 'Raro'),
('Armadura de Cuero',    'Ligera pero protectora.',                               60, 2, 30, 0,  0,  0, 'Común'),
('Cota de Malla',        'Protección media de acero.',                           150, 2, 60, 0,  0,  0, 'Raro'),
('Manto del Mago',       'Aumenta la resistencia mágica.',                       110, 2, 20, 0,  4,  0, 'Raro'),
('Poción de Vida',       'Restaura 50 puntos de vida.',                           20, 3, 50, 0,  0,  0, 'Común'),
('Poción de Maná',       'Restaura 40 puntos de maná.',                          20, 3,  0, 0,  0,  0, 'Común'),
('Poción Grande de Vida','Restaura 120 puntos de vida.',                          60, 3,120, 0,  0,  0, 'Raro'),
('Elixir Supremo',       'Restaura vida y maná al máximo.',                     200, 3,999, 0,  0,  0, 'Legendario'),
('Anillo de Poder',      'Aumenta todos los atributos ligeramente.',             180, 4, 15, 2,  2,  2, 'Épico'),
('Amuleto del Sabio',    'Potencia la inteligencia del portador.',               160, 4,  0, 0,  6,  0, 'Épico'),
('Escudo de Roble',      'Escudo básico de madera reforzada.',                    40, 5, 20, 0,  0,  0, 'Común'),
('Escudo de Hierro',     'Sólida protección de forja enana.',                   100, 5, 50, 3,  0,  0, 'Raro');

-- Enemigos
INSERT INTO Enemigos (nombre, nivel, vida_max, dano_base, exp_recom, oro_recom, descripcion) VALUES
('Rata Gigante',      1,  20,  3,  10,  2, 'Roedor mutado de las alcantarillas.'),
('Goblin Ladrón',     2,  35,  6,  25,  8, 'Criatura ágil que roba oro.'),
('Orco Guerrero',     4,  80, 12,  60, 20, 'Soldado de horda ferozmente leal.'),
('Esqueleto Arquero', 3,  50,  9,  40, 12, 'No-muerto que dispara desde lejos.'),
('Troll del Pantano', 6, 150, 20, 120, 40, 'Regenera vida cada turno.'),
('Dragón Joven',      9, 400, 45, 500,150, 'Cría de dragón con aliento de fuego.'),
('Liche Antiguo',    10, 300, 38, 450,130, 'Mago no-muerto de poder sin igual.'),
('Ogro Berserker',    5, 120, 17,  90, 30, 'Gigante de rabia incontenible.'),
('Vampiro Noble',     8, 250, 30, 350,100, 'Señor de la oscuridad inmortal.'),
('Elemental de Fuego',7, 200, 28, 250, 70, 'Espíritu de llamas invocado.');

-- Personajes de ejemplo
INSERT INTO Personajes (nombre, nivel, exp, oro, vida_max, vida_actual, mana_max, mana_actual, fuerza, agilidad, inteligencia, id_raza, id_clase) VALUES
('Aragorn',  5, 1200, 320, 210, 210,  60,  60, 20, 14, 12, 1, 1),
('Gandalf',  7, 3500, 180, 110, 110, 220, 220, 10, 11, 22, 2, 2),
('Legolas',  6, 2100, 250, 150, 150, 100, 100, 14, 22, 16, 2, 8),
('Thorin',   4,  900, 400, 190, 190,  40,  40, 22, 10, 10, 3, 1);

-- Habilidades iniciales de los personajes
INSERT INTO Personajes_Habilidades (id_personaje, id_habilidad, nivel_actual) VALUES
(1, 1, 3), (1, 2, 2), (1, 3, 1), (1, 6, 2),
(2, 8, 4), (2, 9, 3), (2, 10, 2), (2, 13, 1),
(3,17, 3), (3,18, 2), (3,20, 2),
(4, 1, 2), (4, 2, 3), (4, 6, 1);

-- Inventarios iniciales
INSERT INTO Inventarios (id_personaje, id_item, cantidad, equipado) VALUES
(1,  1, 1, TRUE),  -- Aragorn lleva Espada Corta equipada
(1,  6, 1, TRUE),  -- Aragorn lleva Armadura de Cuero
(1,  9, 3, FALSE), -- 3 Pociones de Vida
(2,  3, 1, TRUE),  -- Gandalf lleva Báculo Arcano
(2,  8, 1, TRUE),  -- Gandalf lleva Manto del Mago
(2, 10, 2, FALSE), -- 2 Pociones de Maná
(3,  1, 1, TRUE),
(4,  2, 1, TRUE),  -- Thorin lleva Hacha de Batalla
(4, 15, 1, TRUE);  -- Thorin lleva Escudo de Roble

-- Logros
INSERT INTO Logros (nombre, descripcion, icono, condicion) VALUES
('Primer Golpe',        'Completa tu primer combate.',                             '⚔️',  'combates >= 1'),
('Cazador de Goblins',  'Derrota a 10 goblins.',                                   '🗡️',  'enemigos_tipo=goblin >= 10'),
('Maestro de la Magia', 'Sube una habilidad mágica al nivel máximo.',              '✨',  'habilidad_magica.nivel = nivel_maximo'),
('Millonario',          'Acumula 1000 monedas de oro.',                            '💰',  'oro >= 1000'),
('Leyenda',             'Alcanza el nivel 10.',                                    '👑',  'nivel >= 10'),
('Coleccionista',       'Reúne 20 objetos distintos en el inventario.',            '🎒',  'items_distintos >= 20'),
('Sin Rasguños',        'Gana un combate sin recibir daño.',                       '🛡️',  'dano_recibido_combate = 0'),
('Árbol Podado',        'Desbloquea una habilidad ultimate.',                      '🌳',  'habilidad_ultimate desbloqueada');
