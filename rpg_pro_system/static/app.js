/* ==========================================================================
   XRPG GUILD MASTER — CLIENT LOGIC (static/app.js)
   ========================================================================== */

// Inicializa la conexión en tiempo real con el servidor mediante WebSockets (Socket.io)
const socket = io();

/* ==========================================================================
   ELEMENTOS DEL DOM (Selectores globales de la interfaz)
   ========================================================================== */
// Elementos de estado de la conexión en red
const dot = document.getElementById('status-dot');         // Punto visual de estado (verde/rojo)
const text = document.getElementById('status-text');       // Texto descriptivo de la conexión
const logBox = document.getElementById('log');             // Caja de texto tipo terminal para el historial de acciones

// Elementos de la sección de visualización de héroes
const contenedor = document.getElementById('contenedor-personajes'); // Grid donde se inyectan las tarjetas HTML
const contadorPersonajes = document.getElementById('contador-personajes'); // Label que muestra la cantidad de héroes
const btnRecargar = document.getElementById('btn-recargar'); // Botón para volver a pedir la lista al servidor

// Selector superior y panel lateral de detalle del personaje seleccionado
const menuPersonajes = document.getElementById('menu-personajes'); // Elemento HTML <select> para alternar personajes
const personajeSeleccionado = document.getElementById('personaje-seleccionado'); // Contenedor del panel lateral
const selectedName = document.getElementById('selected-name');     // Nodo de texto para el nombre en el panel
const selectedLevel = document.getElementById('selected-level');   // Nodo de texto para el nivel en el panel
const selectedGold = document.getElementById('selected-gold');     // Nodo de texto para el oro en el panel
const selectedHealth = document.getElementById('selected-health'); // Nodo de texto para la vida en el panel
const selectedClass = document.getElementById('selected-class');   // Nodo de texto para la clase en el panel
const selectedAvatar = document.querySelector('.selected-avatar'); // Contenedor circular del avatar (primera letra)

// HUD dinámico superior del héroe activo en juego
const heroHud = document.getElementById('hero-hud');       // Contenedor general del HUD (barra superior)
const hudAvatar = document.getElementById('hud-avatar');   // Inicial del avatar en la barra superior
const hudName = document.getElementById('hud-name');       // Nombre del héroe en la barra superior
const hudLevel = document.getElementById('hud-level');     // Nivel del héroe en la barra superior
const hudGold = document.getElementById('hud-gold');       // Oro actual en la barra superior
const hudHp = document.getElementById('hud-hp');           // Texto de vida actual/máxima en la barra superior

// Componentes del Árbol de Habilidades
const skillTree = document.getElementById('skill-tree');   // Contenedor flex/grid donde se renderizan los nodos
const badgeClase = document.getElementById('badge-clase'); // Etiqueta superior que indica la clase del árbol visualizado

// Componentes de la Tienda de Objetos
const shopGrid = document.getElementById('shop-grid');     // Grid que aloja los productos a la venta
const badgeOro = document.getElementById('badge-oro');       // Contador de oro dedicado dentro de la pestaña tienda

// Componentes de la Arena de Combate
const menuEnemigos = document.getElementById('menu-enemigos');       // Selector <select> para elegir contra quién luchar
const btnIniciarCombate = document.getElementById('btn-iniciar-combate'); // Botón disparador del encuentro
const combatArena = document.getElementById('combat-arena');         // Contenedor de la interfaz activa de pelea
const combatActions = document.getElementById('combat-actions');     // Panel de botones de acción (Atacar, Especial...)
const combatLog = document.getElementById('combat-log');             // Log específico e interno de la pelea
const badgeTurno = document.getElementById('badge-turno');           // Indicador de texto de quién tiene la iniciativa

// Componentes del Inventario / Mochila
const inventoryGrid = document.getElementById('inventory-grid');     // Contenedor de ranuras de objetos equipados/guardados
const badgeItems = document.getElementById('badge-items');           // Contador del total de objetos en posesión

/* ==========================================================================
   ESTADO DE LA APLICACIÓN (Memoria caché del cliente)
   ========================================================================== */
let personajesActuales = [];  // Array con todos los personajes del usuario devueltos por el socket
let enemigosActuales = [];    // Lista de monstruos o contrincantes disponibles en la base de datos
let itemsActuales = [];       // Listado general de ítems del juego
let personajeActivo = null;   // Objeto literal del personaje seleccionado actualmente por el jugador
let combateState = null;      // Estructura de control del combate en curso (instancia de la pelea, vida del enemigo, etc.)

// Diccionario estático para mapear las claves foráneas (IDs de base de datos) con cadenas de texto legibles
const NOMBRES_CLASES = {
    1: 'Guerrero', 2: 'Mago', 3: 'Pícaro', 4: 'Paladín',
    5: 'Druida', 6: 'Bárbaro', 7: 'Clérigo', 8: 'Ranger',
    9: 'Bardo', 10: 'Brujo', 11: 'Hechicero', 12: 'Monje'
};

/* ==========================================================================
   FUNCIONES ÚTILES Y AUXILIARES
   ========================================================================== */

/**
 * Añade de forma progresiva una nueva línea al historial de logs del sistema.
 * @param {string} mensaje - Cadena de texto o código HTML seguro a imprimir.
 */
function escribirLog(mensaje) {
    if (!logBox) return; // Cláusula de salvaguarda por si el nodo del DOM no existe

    // Creamos un nuevo nodo párrafo para evitar la sobrecarga de repintar todo el contenedor con innerHTML
    const linea = document.createElement('p');
    linea.className = 'log-line'; // Inyección de clase CSS para el control de estilos de la terminal
    linea.innerHTML = `<span class="log-prompt">&gt;</span> ${mensaje}`; // Estructura con el prompt clásico ">"

    // Añadimos el nodo al final de la lista
    logBox.appendChild(linea);

    // Desplazamiento automático (Autoscroll): Fuerza al contenedor a bajar al píxel más bajo
    logBox.scrollTop = logBox.scrollHeight;
}

/**
 * Muestra una notificación emergente temporal (Toast) en la pantalla.
 * @param {string} mensaje - Texto a mostrar.
 * @param {string} tipo - Categoría del aviso ('error', 'warn', 'ok'). Controla el color por CSS.
 */
function mostrarToast(mensaje, tipo = 'error') {
    // Elimina cualquier Toast previo activo para evitar que se acumulen verticalmente en la pantalla
    document.querySelectorAll('.toast').forEach(t => t.remove());

    // Construcción del elemento contenedor del Toast
    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    toast.innerText = mensaje;

    // Inyección en la raíz del documento y temporizador de destrucción a los 3 segundos (3000ms)
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

/**
 * Emite un evento a través de WebSockets para requerir la lista actualizada de personajes al backend.
 */
function pedirPersonajes() {
    escribirLog("Solicitando aventureros al servidor...");
    socket.emit('obtener_personajes'); // Dispara el listener del backend encargado de hacer la consulta SQL
}

/**
 * Normaliza la obtención del parámetro de vida máxima mitigando discrepancias de nombres en las propiedades del objeto.
 * @param {Object} p - Objeto del personaje.
 * @returns {number} Valor numérico de los puntos de vida máximos.
 */
function getVidaMax(p) {
    return Number(p.vida_max || p.vida_maxima || 100);
}

/**
 * Genera un número entero aleatorio comprendido dentro de un rango cerrado.
 * @param {number} min - Límite inferior inclusivo.
 * @param {number} max - Límite superior inclusivo.
 * @returns {number} Entero resultante.
 */
function rand(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/* ==========================================================================
   NAVEGACIÓN (SISTEMA DE PESTAÑAS)
   ========================================================================== */
// Asigna los escuchadores de clics a todos los elementos clasificados como botones de pestaña
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Resetea el estado visual activo eliminando la clase '.active' de todas las pestañas y contenidos
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Aplica el estado activo exclusivamente al botón pulsado
        btn.classList.add('active');

        // Localiza el contenedor de contenido correspondiente usando el atributo 'data-tab' e inyecta la clase activa
        const tabContent = document.getElementById('tab-' + btn.dataset.tab);
        if (tabContent) tabContent.classList.add('active');
    });
});

// Atajo o redirección de UX para saltar directamente a la pestaña de combates
const btnIrCombate = document.getElementById('btn-ir-combate');
if (btnIrCombate) {
    btnIrCombate.addEventListener('click', () => {
        // Simula un clic nativo sobre el botón del menú que posee el data-tab de combate
        const tabCombate = document.querySelector('[data-tab="combate"]');
        if (tabCombate) tabCombate.click();

        // Hace un desplazamiento vertical fluido hasta enfocar el panel de juego principal
        const tabsPanel = document.querySelector('.tabs-panel');
        if (tabsPanel) tabsPanel.scrollIntoView({ behavior: 'smooth' });
    });
}

/* ==========================================================================
   GESTIÓN DE PERSONAJES (Selección y Sincronización del HUD)
   ========================================================================== */

/**
 * Realiza una petición asíncrona al backend de Flask para obtener las estadísticas
 * finales calculadas y balanceadas de la base de datos de PostgreSQL.
 * @param {number|string} idPersonaje - ID del personaje a consultar.
 */
function cargarPanelEstadisticas(idPersonaje) {
    fetch(`/api/personajes/${idPersonaje}/estadisticas`)
        .then(response => {
            if (!response.ok) throw new Error("No se pudieron obtener las estadísticas.");
            return response.json();
        })
        .then(data => {
            if (!data) return;

            // 1. Sincronizar textos del HUD superior clásico y la tarjeta pequeña
            if (selectedHealth) selectedHealth.innerText = `Vida: ${data.vida_actual}/${data.vida_max}`;
            if (hudHp) hudHp.innerText = `${data.vida_actual}/${data.vida_max}`;

            // Actualización de referencias en la memoria global por seguridad
            if (personajeActivo) {
                personajeActivo.vida_actual = data.vida_actual;
                personajeActivo.vida_max = data.vida_max;
                personajeActivo.fuerza = data.fuerza;
                personajeActivo.agilidad = data.agilidad;
                personajeActivo.inteligencia = data.inteligencia;
            }

            // =========================================================
            // 🎯 CONTROL DE VISIBILIDAD DE PANELES SEPARADOS
            // =========================================================
            const emptyState = document.getElementById('stats-empty-state');
            const hudWrapper = document.getElementById('stats-hud-wrapper');

            if (emptyState) emptyState.classList.add('hidden');
            if (hudWrapper) hudWrapper.classList.remove('hidden');

            // =========================================================
            // 📊 SINCRONIZACIÓN DE BARRAS DE ESTADO DINÁMICAS
            // =========================================================
            // Rellenar barra de Vida Real recalculada
            const hpText = document.getElementById('real-hp-text');
            const hpFill = document.getElementById('real-hp-fill');
            if (hpText) hpText.innerText = `${data.vida_actual} / ${data.vida_max}`;
            if (hpFill) {
                const pctHp = (data.vida_actual / data.vida_max) * 100;
                hpFill.style.width = `${pctHp}%`;
            }

            // Rellenar recurso dinámico (Maná, Ira, Energía...) según devuelva Python
            const resourceName = document.getElementById('real-resource-name');
            const mpText = document.getElementById('real-mp-text');
            const mpFill = document.getElementById('real-mp-fill');

            const tipoRecurso = data.recurso_primario || 'Maná';
            if (resourceName) resourceName.innerText = `✨ ${tipoRecurso.toUpperCase()}`;
            if (mpText) mpText.innerText = `${data.mana_actual} / ${data.mana_max}`;
            if (mpFill) {
                const pctMana = data.mana_max > 0 ? (data.mana_actual / data.mana_max) * 100 : 0;
                mpFill.style.width = `${pctMana}%`;
            }

            // =========================================================
            // ⚔️ SINCRONIZACIÓN DE HOJA DE ATRIBUTOS
            // =========================================================
            const txtFuerza = document.getElementById('stat-fuerza');
            const txtAgilidad = document.getElementById('stat-agilidad');
            const txtInteligencia = document.getElementById('stat-inteligencia');

            if (txtFuerza) txtFuerza.innerText = data.fuerza ?? 10;
            if (txtAgilidad) txtAgilidad.innerText = data.agilidad ?? 10;
            if (txtInteligencia) txtInteligencia.innerText = data.inteligencia ?? 10;

            if (typeof escribirLog === 'function') {
                escribirLog(`Atributos reales y barras HUD sincronizadas.`);
            }
        })
        .catch(error => console.error("❌ Error en estadísticas:", error));
}


/**
 * Rellena de forma dinámica el menú desplegable <select> con las opciones de personajes del usuario.
 * @param {Array} lista - Array conteniendo los objetos de cada personaje.
 */
function llenarMenuPersonajes(lista) {
    if (!menuPersonajes) return;
    // Resetea el menú con una opción por defecto para evitar duplicaciones al recargar
    menuPersonajes.innerHTML = '<option value="">Selecciona un aventurero...</option>';

    lista.forEach((p) => {
        const option = document.createElement('option');
        option.value = p.id;
        option.textContent = `${p.nombre || "Aventurero"} — Nivel ${p.nivel ?? 1}`;
        menuPersonajes.appendChild(option);
    });
}

/**
 * Activa un personaje en el cliente y propaga sus estadísticas por todos los componentes de la interfaz.
 * @param {number|string} idPersonaje - Identificador único del personaje a seleccionar.
 */
function seleccionarPersonaje(idPersonaje) {
    // Busca el objeto del personaje en la memoria cache local
    const personaje = personajesActuales.find(p => String(p.id) === String(idPersonaje));

    // Desmarca visualmente cualquier tarjeta de personaje seleccionada previamente
    document.querySelectorAll('.card-personaje').forEach(card => card.classList.remove('selected'));

    // CLÁUSULA DE SALVAGUARDA
    if (!personaje) {
        if (personajeSeleccionado) personajeSeleccionado.classList.add('hidden');
        if (heroHud) heroHud.classList.add('hidden');
        if (skillTree) skillTree.innerHTML = `<div class="empty-state"><span>🪄</span><p>Selecciona un personaje para ver su progreso.</p></div>`;
        if (inventoryGrid) inventoryGrid.innerHTML = `<div class="empty-state"><span>🎒</span><p>Mochila vacía.</p></div>`;
        if (badgeOro) badgeOro.innerText = `💰 0 oro`;
        if (badgeItems) badgeItems.innerText = `0 objetos`;

        const contenedorStats = document.getElementById('stats-detail-container');
        if (contenedorStats) {
            contenedorStats.innerHTML = `
                <div class="empty-state">
                    <span aria-hidden="true">📊</span>
                    <p>Selecciona un aventurero para calcular su daño, maná y estadísticas de combate.</p>
                </div>`;
        }

        personajeActivo = null;
        escribirLog("Ningún personaje seleccionado.");
        return;
    }

    // Guarda la referencia del personaje activo de forma global
    personajeActivo = personaje;

    // Remarca visualmente la tarjeta de personaje
    const card = document.querySelector(`[data-personaje-id="${personaje.id}"]`);
    if (card) card.classList.add('selected');

    // Desestructuración manual de datos iniciales
    const inicial = (personaje.nombre || "?").charAt(0).toUpperCase();
    const claseNombre = NOMBRES_CLASES[personaje.id_clase] || 'Aventurero';

    // Sincronización y actualización de datos en el Panel de Detalle Lateral
    if (selectedAvatar) selectedAvatar.innerText = inicial;
    if (selectedName) selectedName.innerText = personaje.nombre || "Aventurero";
    if (selectedLevel) selectedLevel.innerText = `Nivel: ${personaje.nivel ?? 1}`;
    if (selectedGold) selectedGold.innerText = `Oro: ${personaje.oro ?? 0}`;
    if (selectedClass) selectedClass.innerText = `Clase: ${claseNombre}`;
    if (personajeSeleccionado) personajeSeleccionado.classList.remove('hidden');

    // Sincronización y actualización de datos en la barra de HUD superior global
    if (hudAvatar) hudAvatar.innerText = inicial;
    if (hudName) hudName.innerText = personaje.nombre || "Aventurero";
    if (hudLevel) hudLevel.innerText = personaje.nivel ?? 1;
    if (hudGold) hudGold.innerText = personaje.oro ?? 0;
    if (heroHud) heroHud.classList.remove('hidden');

    // ⏳ MODIFICACIÓN: Ponemos un estado de carga temporal en lo que responde el servidor
    if (selectedHealth) selectedHealth.innerText = `Vida: ...`;
    if (hudHp) hudHp.innerText = `...`;

    // Carga de módulos dependientes
    cargarHabilidades(personaje.id_clase, claseNombre);
    cargarInventario(personaje.id);

    // 🚀 ¡PETICIÓN PRINCIPAL! Calculamos estadísticas reales desde el Backend
    cargarPanelEstadisticas(personaje.id);


    if (badgeOro) badgeOro.innerText = `💰 ${personaje.oro ?? 0} oro`;
    escribirLog(`Personaje seleccionado: ${personaje.nombre}.`);
}

// Vincula el evento de cambio en el selector desplegable <select> superior
if (menuPersonajes) {
    menuPersonajes.addEventListener('change', () => seleccionarPersonaje(menuPersonajes.value));
}

/* ==========================================================================
   ÁRBOL DE HABILIDADES (Consumo de API REST, Renderizado e Incrementos)
   ========================================================================== */

/**
 * Consulta mediante AJAX las habilidades asignadas a la clase del héroe actual.
 * @param {number} claseId - ID de la clase en base de datos.
 * @param {string} claseNombre - Nombre textual traducido de la clase.
 */
async function cargarHabilidades(claseId, claseNombre) {
    if (!skillTree) return;
    badgeClase.innerText = claseNombre || 'Sin clase';
    skillTree.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando habilidades...</p></div>`;

    // Doble verificación de seguridad sobre el estado global del héroe activo
    if (!personajeActivo) {
        skillTree.innerHTML = `<div class="empty-state"><span>🪄</span><p>Selecciona un personaje para ver su progreso.</p></div>`;
        return;
    }

    try {
        // Ejecuta una petición HTTP GET con parámetros de consulta de la clase y el personaje específico
        const res = await fetch(`/api/personajes/arbol-habilidades?clase_id=${claseId}&personaje_id=${personajeActivo.id}`);
        const habilidades = await res.json();

        // Si la respuesta no es un array válido o carece de elementos, aborta e informa en la vista
        if (!Array.isArray(habilidades) || habilidades.length === 0) {
            skillTree.innerHTML = `<div class="empty-state"><span>📭</span><p>Sin habilidades para esta clase.</p></div>`;
            return;
        }

        // Delega la responsabilidad de pintar el árbol a la función encargada del pintado HTML
        renderArbolHabilidades(habilidades);
    } catch (err) {
        skillTree.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando habilidades.</p></div>`;
    }
}

/**
 * Genera el mapa HTML del árbol de habilidades y añade los controladores de eventos a sus botones.
 * @param {Array} habilidades - Colección de habilidades obtenidas del servidor.
 */
function renderArbolHabilidades(habilidades) {
    // Diccionario de pesos de ordenación para estructurar el árbol lógicamente (Pasivas -> Activas -> Ultimates)
    const orden = { 'pasiva': 0, 'activa': 1, 'ultimate': 2 };
    habilidades.sort((a, b) => (orden[a.tipo] ?? 1) - (orden[b.tipo] ?? 1));

    // Mapea e inyecta la plantilla HTML literal de forma dinámica
    skillTree.innerHTML = habilidades.map((h, idx) => {
        const tipo = h.tipo || 'activa';

        // Selección condicional del icono representativo según la categoría
        let icono = '✨';
        if (tipo === 'pasiva') icono = '🛡️';
        if (tipo === 'ultimate') icono = '🔥';

        // Formateo condicional de textos según consuma maná o actúe como un beneficio pasivo
        const manaTexto = h.costo_mana > 0 ? `💧 <b>${h.costo_mana} MP</b>` : '✨ <b>Pasiva</b>';
        const danoTexto = h.dano_base > 0 ? `⚔️ <b>${h.dano_base} Poder</b>` : '📜 <b>Efecto</b>';

        // Control y chequeo de límites de nivel para inhabilitar mejoras futuras
        const nivelActual = h.nivel_actual ?? 0;
        const nivelMaximo = h.nivel_maximo ?? 1;
        const esMaximo = nivelActual >= nivelMaximo;

        // Añade una flecha conectora visual entre nodos excepto para la última habilidad del array
        const arrow = idx < habilidades.length - 1 ? `<span class="skill-arrow">➜</span>` : '';

        return `
            <div class="skill ${tipo} ${esMaximo ? 'skill-maxed' : ''}" data-skill-id="${h.id}">
                <div class="skill-header">
                    <span class="skill-icon">${icono}</span>
                    <span class="skill-level-badge">Lv ${nivelActual}/${nivelMaximo}</span>
                </div>
                
                <h4 class="skill-title">${h.nombre}</h4>
                <p class="skill-desc">${h.descripcion || 'Sin descripción disponible.'}</p>
                
                <div class="skill-stats">
                    <div class="stat-box">
                        <span>Coste</span>
                        ${manaTexto}
                    </div>
                    <div class="stat-box">
                        <span>Poder Base</span>
                        ${danoTexto}
                    </div>
                    <div class="stat-box">
                        <span>Categoría</span>
                        <b class="type-txt">${tipo.toUpperCase()}</b>
                    </div>
                </div>
                
                <button class="btn-mejorar-habilidad" 
                        data-skill-id="${h.id}" 
                        ${esMaximo ? 'disabled' : ''}>
                    ${esMaximo ? '✅ Máximo Nivel' : '⬆️ Mejorar Habilidad'}
                </button>
            </div>
            ${arrow}
        `;
    }).join(''); // Convierte el array resultante en una cadena compacta de HTML

    // Vincula un escuchador de clics individual a cada botón inyectado en el árbol
    skillTree.querySelectorAll('.btn-mejorar-habilidad').forEach(btn => {
        btn.addEventListener('click', () => {
            mejorarHabilidad(btn.dataset.skillId);
        });
    });
}

/**
 * Realiza una mutación POST hacia el servidor para intentar incrementar el nivel de una habilidad seleccionada.
 * @param {number|string} idHabilidad - Identificador de la habilidad que se quiere actualizar.
 */
async function mejorarHabilidad(idHabilidad) {
    // Cláusula de salvaguarda: Impide la llamada al endpoint si no hay un héroe activo seleccionado
    if (!personajeActivo) {
        escribirLog("Selecciona un héroe antes de mejorar habilidades.");
        return;
    }
    try {
        const res = await fetch('/api/habilidad/subir-nivel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id_personaje: personajeActivo.id,
                id_habilidad: idHabilidad
            })
        });
        const resultado = await res.json();

        // Control de validaciones fallidas en las reglas de negocio del backend
        if (!resultado.ok) {
            // Caso A: El servidor detecta dependencias o requisitos del árbol de habilidades no cumplidos
            if (resultado.requisites_faltantes?.length) {
                const lista = resultado.requisites_faltantes
                    .map(r => `${r.nombre} (necesitas Lv ${r.nivel_necesario}, tienes Lv ${r.nivel_actual})`)
                    .join(' | ');
                escribirLog(`Requisitos faltantes: ${lista}`);
                mostrarToast(`Requisitos: ${lista}`, 'warn');
            } else {
                // Caso B: Errores genéricos (Ej. falta de puntos de habilidad, nivel de personaje insuficiente)
                escribirLog(resultado.mensaje);
                mostrarToast(resultado.mensaje, 'warn');
            }
            return;
        }

        // Mutación local y reactiva del DOM (Optimistic/Reactive Update) para actualizar la tarjeta sin re-renderizar todo
        const hab = resultado.habilidad;
        const nodo = document.querySelector(`[data-skill-id="${hab.id}"]`);
        if (nodo) {
            let badge = nodo.querySelector('.skill-level-badge');
            // Si el nodo de nivel no existiera por algún motivo, lo crea al vuelo de forma dinámica
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'skill-level-badge';
                nodo.prepend(badge);
            }
            // Sincroniza el nivel del nodo visual con el nuevo valor del backend
            badge.innerText = `Lv ${hab.nivel_actual}/${hab.nivel_maximo}`;

            // Si alcanza los límites máximos establecidos, bloquea el botón de acción
            if (hab.nivel_actual >= hab.nivel_maximo) {
                nodo.classList.add('skill-maxed');
                const btn = nodo.querySelector('.btn-mejorar-habilidad');
                if (btn) { btn.disabled = true; btn.innerText = '✅ Máximo Nivel'; }
            }
        }

        // Envía retroalimentación visual al log y al sistema de notificaciones de la pantalla
        escribirLog(resultado.mensaje);
        mostrarToast(resultado.mensaje, 'ok');

    } catch (err) {
        escribirLog("Error de red al mejorar la habilidad.");
        console.error(err);
    }
}
/* ==========================================================================
   TIENDA COMERCIAL (Consumo de API REST, Filtros y Transacciones)
   ========================================================================== */

/**
 * Consulta los artículos del catálogo de la tienda filtrando opcionalmente por su rareza.
 * @param {string} rareza - Criterio de filtrado ('común', 'raro', 'épico', etc.) o vacío para todos.
 */
async function cargarTienda(rareza = '') {
    if (!shopGrid) return; // Salvaguarda si el grid de la tienda no se encuentra en el DOM

    // Inyecta el estado visual de carga antes de iniciar la petición asíncrona
    shopGrid.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando objetos...</p></div>`;

    try {
        // Construye de forma dinámica la URL aplicando codificación de caracteres seguros si hay filtro
        const url = rareza ? `/api/items/?rareza=${encodeURIComponent(rareza)}` : '/api/items/';
        const res = await fetch(url);
        itemsActuales = await res.json(); // Actualiza la caché en memoria local de ítems

        // Actualiza el indicador global KPI con el total de artículos en catálogo
        const kpiItems = document.getElementById('kpi-items');
        if (kpiItems) kpiItems.innerText = itemsActuales.length;

        // Si la consulta devuelve un catálogo vacío, renderiza el estado correspondiente
        if (!itemsActuales.length) {
            shopGrid.innerHTML = `<div class="empty-state"><span>📦</span><p>Sin objetos disponibles.</p></div>`;
            return;
        }

        // Mapea la colección de ítems a sus respectivas estructuras de tarjetas HTML
        shopGrid.innerHTML = itemsActuales.map(it => {
            const rar = (it.rareza || 'Común').toLowerCase(); // Formatea la clase CSS de rareza
            const stats = it.stats || {};

            // Procesa el diccionario de estadísticas filtrando propiedades vacías o nulas
            const statsHtml = Object.entries(stats)
                .filter(([_, v]) => v && Number(v) !== 0) // Omite estadísticas en 0
                .map(([k, v]) => `<span>${k}: <b>+${v}</b></span>`)
                .join('');

            return `
                <div class="shop-item rar-${rar}" data-item-id="${it.id}">
                    <div class="shop-item-top">
                        <span class="shop-icon">📦</span>
                        <span class="shop-rar">${it.rareza || 'Común'}</span>
                    </div>
                    <h4>${it.nombre}</h4>
                    <p>${it.descripcion || ''}</p>
                    <div class="shop-stats">${statsHtml || '<span>Sin bonus</span>'}</div>
                    <div class="shop-bottom">
                        <span class="shop-price">💰 ${it.precio}</span>
                        <button class="btn-comprar-item" data-item-id="${it.id}">Comprar</button>
                    </div>
                </div>
            `;
        }).join(''); // Compacta el array mapeado en una cadena HTML única

        // Asigna un escuchador de eventos individual para interceptar las intenciones de compra
        shopGrid.querySelectorAll('.btn-comprar-item').forEach(btn => {
            btn.addEventListener('click', () => comprarItem(Number(btn.dataset.itemId)));
        });

    } catch (err) {
        // Captura excepciones de red o fallos de parseo e informa visualmente
        shopGrid.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando la tienda.</p></div>`;
    }
}

/**
 * Procesa la transacción de compra de un ítem validando fondos en cliente y persistiendo en el backend.
 * @param {number} itemId - Identificador único del objeto comercializable.
 */
async function comprarItem(itemId) {
    // Salvaguarda: Bloquea compras anónimas si el usuario no ha inicializado un aventurero activo
    if (!personajeActivo) {
        escribirLog("Selecciona un héroe antes de comprar.");
        return;
    }

    // Localiza el objeto correspondiente dentro de la caché local de la tienda
    const item = itemsActuales.find(i => i.id === itemId);
    if (!item) return;

    // Validación previa en cliente (Pre-check UX) para mitigar peticiones innecesarias al backend
    if ((personajeActivo.oro ?? 0) < item.precio) {
        escribirLog(`No tienes oro suficiente para ${item.nombre}.`);
        mostrarToast("No tienes oro suficiente", "warn");
        return;
    }

    try {
        // Realiza la petición mutativa POST al controlador de tienda en Flask
        const res = await fetch('/api/tienda/comprar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id_personaje: personajeActivo.id,
                id_item: itemId
            })
        });

        const resultado = await res.json();

        // Si el backend deniega la transacción por discrepancia de datos, rompe el flujo
        if (!resultado.ok) {
            escribirLog(resultado.mensaje);
            mostrarToast(resultado.mensaje, 'warn');
            return;
        }

        // Sincroniza el estado local y las referencias cruzadas con el balance real del backend
        personajeActivo.oro = resultado.oro_restante;
        const refLista = personajesActuales.find(p => p.id === personajeActivo.id);
        if (refLista) refLista.oro = personajeActivo.oro;

        // Propaga el nuevo balance de oro a lo largo de todos los nodos vinculados de la UI
        if (hudGold) hudGold.innerText = personajeActivo.oro;
        if (selectedGold) selectedGold.innerText = `Oro: ${personajeActivo.oro}`;
        if (badgeOro) badgeOro.innerText = `💰 ${personajeActivo.oro} oro`;

        escribirLog(`¡Compra confirmada! Has adquirido ${item.nombre} por ${item.precio} de oro.`);
        mostrarToast(`Comprado: ${item.nombre}`, 'ok');

        // Lanza re-consultas asíncronas inmediatas para refrescar la mochila y sincronizar cards en paralelo
        cargarInventario(personajeActivo.id);
        pedirPersonajes();

    } catch (err) {
        escribirLog("Error de red al realizar la compra.");
        console.error(err);
    }
}

// Vincula los filtros por categorías (Chips) para alternar el catálogo de la tienda de forma reactiva
document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active'); // Destaca visualmente el filtro activo
        cargarTienda(chip.dataset.rareza); // Recarga la tienda aplicando el atributo de datos correspondiente
    });
});

/* ==========================================================================
   INVENTARIO MOCHILA (Visualización de Equipamiento del Héroe)
   ========================================================================== */

/**
 * Recupera e inyecta en el DOM las pertenencias reales del héroe activo en sesión.
 * @param {number} personajeId - ID único del personaje.
 */
async function cargarInventario(personajeId) {
    if (!inventoryGrid) return;
    inventoryGrid.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando mochila...</p></div>`;

    try {
        const res = await fetch(`/api/inventario/?id=${personajeId}`);
        const items = await res.json();

        // Actualiza el indicador textual aplicando reglas básicas de pluralización
        if (badgeItems) badgeItems.innerText = `${items.length} objeto${items.length === 1 ? '' : 's'}`;

        // Si la mochila está vacía, renderiza su correspondiente aviso visual
        if (!items.length) {
            inventoryGrid.innerHTML = `<div class="empty-state"><span>🎒</span><p>Mochila vacía.</p></div>`;
            return;
        }

        // Recorre los ítems de la mochila mapeándolos a componentes visuales dedicados
        inventoryGrid.innerHTML = items.map(it => {
            const rar = (it.rareza || 'Común').toLowerCase();
            return `
                <div class="inv-item rar-${rar} ${it.equipado ? 'equipped' : ''}">
                    <div class="inv-icon">⚔️</div>
                    <strong>${it.item_nombre}</strong>
                    <span class="inv-rar">${it.rareza}</span>
                    <p>x${it.cantidad}</p>
                    ${it.equipado ? '<span class="equipped-tag">Equipado</span>' : ''}
                </div>
            `;
        }).join('');
    } catch (err) {
        inventoryGrid.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando inventario.</p></div>`;
    }
}

/* ==========================================================================
   ARENA DE COMBATE SIMULADO (Lógica de Turnos, Estado de Juego y Logs)
   ========================================================================== */

/**
 * Consume el endpoint del servidor para rellenar el listado <select> de contrincantes disponibles.
 */
async function cargarEnemigos() {
    if (!menuEnemigos) return;
    try {
        const res = await fetch('/api/enemigos');
        enemigosActuales = await res.json(); // Almacena el catálogo de monstruos en caché de cliente

        // Actualiza el indicador numérico KPI global de enemigos registrados
        const kpiEnemigos = document.getElementById('kpi-enemigos');
        if (kpiEnemigos) kpiEnemigos.innerText = enemigosActuales.length;

        // Construye las opciones del desplegable combinando textos explicativos y estadísticas bases
        menuEnemigos.innerHTML = '<option value="">Selecciona un enemigo...</option>' +
            enemigosActuales.map(e =>
                `<option value="${e.id}">${e.nombre} — Lv ${e.nivel} (${e.vida_max} HP)</option>`
            ).join('');
    } catch {
        menuEnemigos.innerHTML = '<option value="">Error cargando enemigos</option>';
    }
}

// Inicializa el disparador de la instancia de combate aislando el estado local del juego
if (btnIniciarCombate) {
    btnIniciarCombate.addEventListener('click', () => {
        // Validaciones preventivas antes de instanciar la estructura del combate
        if (!personajeActivo) {
            escribirLog("Elige un héroe antes de combatir.");
            return;
        }
        const enemigo = enemigosActuales.find(e => String(e.id) === String(menuEnemigos.value));

        if (!enemigo) {
            escribirLog("Elige un enemigo válido.");
            return;
        }

        // Inicialización y aislamiento del objeto de control del estado del combate actual
        combateState = {
            turno: 1,
            heroe: {
                id: personajeActivo.id,
                nombre: personajeActivo.nombre,
                hp: personajeActivo.vida_actual,
                hpMax: getVidaMax(personajeActivo),
                fuerza: personajeActivo.fuerza ?? 12
            },
            enemigo: {
                id: enemigo.id,
                nombre: enemigo.nombre,
                hp: enemigo.vida_max,
                hpMax: enemigo.vida_max,
                dano: enemigo.dano_base
            },
            defendiendo: false // Flag de control para aplicar modificadores de reducción de daño
        };

        // Rellena las identidades y avatares de la interfaz gráfica de la arena
        document.getElementById('hero-avatar').innerText = (personajeActivo.nombre || '?').charAt(0).toUpperCase();
        document.getElementById('hero-name').innerText = personajeActivo.nombre;
        document.getElementById('enemy-avatar').innerText = '👹';
        document.getElementById('enemy-name').innerText = enemigo.nombre;

        // Visualiza los contenedores del juego y limpia el historial antiguo de batalla
        actualizarBarrasCombate();
        if (combatArena) combatArena.classList.remove('hidden');
        if (combatActions) combatActions.classList.remove('hidden');
        if (combatLog) combatLog.innerHTML = `<p>&gt; ¡${personajeActivo.nombre} desafía a ${enemigo.nombre}!</p>`;
        if (badgeTurno) badgeTurno.innerText = `Turno ${combateState.turno}`;
    });
}

/**
 * Recalcula matemáticamente los porcentajes de vida restantes actualizando las barras de progreso del DOM.
 */
function actualizarBarrasCombate() {
    if (!combateState) return;
    const h = combateState.heroe;
    const e = combateState.enemigo;

    // Calcula y escala de forma segura los anchos de las barras usando una cota inferior de 0%
    document.getElementById('hero-hp-fill').style.width = `${Math.max(0, h.hp / h.hpMax * 100)}%`;
    document.getElementById('hero-hp-text').innerText = `${Math.max(0, h.hp)}/${h.hpMax}`;
    document.getElementById('enemy-hp-fill').style.width = `${Math.max(0, e.hp / e.hpMax * 100)}%`;
    document.getElementById('enemy-hp-text').innerText = `${Math.max(0, e.hp)}/${e.hpMax}`;
}

/**
 * Añade una nueva línea de acciones específica a la caja de texto interna de la arena de combate.
 * @param {string} msg - Texto o cadena formateada a imprimir.
 */
function logCombate(msg) {
    if (!combatLog) return;
    const p = document.createElement('p');
    p.innerHTML = '&gt; ' + msg;
    combatLog.appendChild(p);
    combatLog.scrollTop = combatLog.scrollHeight; // Fuerza scroll vertical automático
}

/**
 * Despacha de forma asíncrona un informe analítico de la acción de combate para su persistencia en base de datos.
 */
function registrarAccionBackend(accion, danoInfligido, danoRecibido, resultado) {
    fetch('/api/combate/registro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            id_personaje: combateState.heroe.id,
            id_enemigo: combateState.enemigo.id,
            turno: combateState.turno,
            accion: accion,
            dano_infligido: danoInfligido,
            dano_recibido: danoRecibido,
            resultado: resultado
        })
    }).catch(() => {}); // Falla silenciosamente en fondo sin interrumpir la fluidez del bucle de juego
}

/**
 * Ejecuta la lógica del turno automático del enemigo calculando daños y mitigaciones aplicadas.
 */
function turnoEnemigo() {
    if (!combateState) return;
    if (combateState.enemigo.hp <= 0) return finalizarCombate('victoria'); // Interrupción preventiva si ha fallecido

    const danoBase = combateState.enemigo.dano;

    // Aplica reducción del 50% si el héroe activó la postura defensiva; si no, añade una pequeña varianza
    const dano = combateState.defendiendo ? Math.max(1, Math.floor(danoBase / 2)) : danoBase + rand(-2, 2);
    combateState.heroe.hp -= dano;

    logCombate(`👹 ${combateState.enemigo.nombre} te golpea por <b>${dano}</b> de daño${combateState.defendiendo ? ' (mitigado)' : ''}.`);
    combateState.defendiendo = false; // Resetea el flag defensivo para el próximo ciclo
    actualizarBarrasCombate();

    // Comprobación de condición de derrota del jugador
    if (combateState.heroe.hp <= 0) return finalizarCombate('derrota');

    // Avanza el turno de juego e incrementa el indicador visual
    combateState.turno++;
    if (badgeTurno) badgeTurno.innerText = `Turno ${combateState.turno}`;
}

// Captura e interpreta el panel de acciones clicables del jugador durante un encuentro activo
if (combatActions) {
    combatActions.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!combateState) return;
            const accion = btn.dataset.accion;

            // Tratamiento específico inmediato en caso de huida voluntaria
            if (accion === 'huir') {
                logCombate(`🏃 Huyes del combate.`);
                registrarAccionBackend('huir', 0, 0, 'huida');
                finalizarCombate('huida');
                return;
            }

            let danoInfligido = 0;
            // Estructura de control condicional según el botón de comando pulsado
            if (accion === 'atacar') {
                danoInfligido = rand(8, 18);
                combateState.enemigo.hp -= danoInfligido;
                logCombate(`🗡️ Atacas a ${combateState.enemigo.nombre} y haces <b>${danoInfligido}</b> de daño.`);
            } else if (accion === 'especial') {
                danoInfligido = rand(18, 32);
                combateState.enemigo.hp -= danoInfligido;
                logCombate(`✨ Lanzas una habilidad especial: <b>${danoInfligido}</b> de daño crítico.`);
            } else if (accion === 'defender') {
                combateState.defendiendo = true;
                logCombate(`🛡️ Adoptas postura defensiva.`);
            }

            actualizarBarrasCombate();

            // Comprobación de fin de combate tras la acción ofensiva del jugador
            if (combateState.enemigo.hp <= 0) {
                registrarAccionBackend(accion, danoInfligido, 0, 'victoria');
                return finalizarCombate('victoria');
            }

            // Continúa el combate delegando el control al enemigo tras un leve retardo asíncrono para dar realismo (600ms)
            registrarAccionBackend(accion, danoInfligido, 0, 'continua');
            setTimeout(turnoEnemigo, 600);
        });
    });
}

/**
 * Limpia y congela la instancia de combate, ocultando los paneles operativos de ataque.
 * @param {string} resultado - Cadena descriptiva del desenlace ('victoria', 'derrota', 'huida').
 */
function finalizarCombate(resultado) {
    if (combatActions) combatActions.classList.add('hidden'); // Cierra los controles operativos
    if (resultado === 'victoria') {
        logCombate(`🏆 <b>¡Victoria!</b> Has derrotado a ${combateState.enemigo.nombre}.`);
    } else if (resultado === 'derrota') {
        logCombate(`💀 <b>Has caído</b> en combate...`);
    } else {
        logCombate(`Combate finalizado.`);
    }
    combateState = null; // Libera la memoria de la variable de control del estado de combate
}

/* ==========================================================================
   SUBIR DE NIVEL GLOBAL (Mutaciones de Atributos mediante API)
   ========================================================================== */

/**
 * Despacha una solicitud POST para forzar la evolución del héroe activo en el sistema.
 */
async function subirNivelPersonaje() {
    if (!personajeActivo) {
        escribirLog("Selecciona un héroe antes de subir nivel.");
        return;
    }
    try {
        const res = await fetch('/api/personaje/subir-nivel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_personaje: personajeActivo.id })
        });
        const resultado = await res.json();

        // Control de errores de validación de negocio en el backend (ej: falta de experiencia acumulada)
        if (!resultado.ok) {
            escribirLog(resultado.mensaje);
            mostrarToast(resultado.mensaje, 'warn');
            return;
        }

        // Mapea y actualiza masivamente los nuevos atributos e incrementos devueltos por el servidor
        const datos = resultado.personaje;
        personajeActivo.nivel        = datos.nivel_actual;
        personajeActivo.vida_max     = datos.vida_max;
        personajeActivo.vida_actual  = datos.vida_actual;
        personajeActivo.fuerza       = datos.fuerza;
        personajeActivo.agilidad     = datos.agilidad;
        personajeActivo.inteligencia = datos.inteligencia;
        personajeActivo.mana_max     = datos.mana_max || personajeActivo.mana_max;
        personajeActivo.mana_actual  = datos.mana_actual || personajeActivo.mana_actual;

        // Sincroniza y re-inyecta de inmediato las estadísticas actualizadas en las vistas concurrentes
        if (hudLevel) hudLevel.innerText       = datos.nivel_actual;
        if (hudHp) hudHp.innerText             = `${datos.vida_actual}/${datos.vida_max}`;
        if (selectedLevel) selectedLevel.innerText   = `Nivel: ${datos.nivel_actual}`;
        if (selectedHealth) selectedHealth.innerText = `Vida: ${datos.vida_actual}/${datos.vida_max}`;

        // Refresca la barra de progreso textual informativa de experiencia
        const expInfo = document.getElementById('exp-info');
        if (expInfo) expInfo.innerText = `EXP: ${datos.exp_restante} / ${datos.exp_para_siguiente_nivel}`;

        escribirLog(resultado.mensaje);
        mostrarToast(resultado.mensaje, 'ok');
        pedirPersonajes(); // Sincroniza las tarjetas del listado global de héroes en el panel izquierdo

    } catch (err) {
        escribirLog("Error de red al subir nivel.");
        console.error(err);
    }
}

// Vincula la ejecución al botón nativo de subida de nivel de la interfaz
const btnSubirNivel = document.getElementById('btn-subir-nivel');
if (btnSubirNivel) {
    btnSubirNivel.addEventListener('click', subirNivelPersonaje);
}

/* ==========================================================================
   RECEPTORES SOCKET.IO (Eventos y Sincronización en Tiempo Real)
   ========================================================================== */

// Evento disparado automáticamente cuando se establece la tubería de red de WebSockets
socket.on('connect', () => {
    if (dot) dot.className = 'dot connected'; // Actualiza el led visual a verde
    if (text) text.innerText = 'Conectado';
    escribirLog("Conectado con éxito al servidor.");

    // Inicializa la carga masiva paralela de datos de inicio de sesión
    pedirPersonajes();
    cargarTienda();
    cargarEnemigos();
});

// Evento interceptor en caso de microcortes o caídas del proceso principal del backend
socket.on('disconnect', () => {
    if (dot) dot.className = 'dot disconnected'; // Modifica el led visual a rojo
    if (text) text.innerText = 'Desconectado';
    escribirLog("Se perdió la conexión con el servidor.");
});

// Receptor genérico para capturar cadenas informativas de logs procedentes de emisiones del servidor
socket.on('status', (data) => escribirLog(data.msg));

// Canal reactivo principal: Escucha e inyecta las actualizaciones en la lista completa de personajes
socket.on('personajes', (lista) => {
    personajesActuales = lista || [];
    if (!contenedor) return;

    // Sincroniza el KPI numérico superior del panel principal
    const kpiHeroes = document.getElementById('kpi-heroes');
    if (kpiHeroes) kpiHeroes.innerText = personajesActuales.length;

    // Manejo de estados de excepción si la cuenta carece por completo de personajes creados
    if (!lista || lista.length === 0) {
        if (menuPersonajes) menuPersonajes.innerHTML = '<option value="">No hay personajes disponibles</option>';
        if (personajeSeleccionado) personajeSeleccionado.classList.add('hidden');
        contenedor.innerHTML = `<div class="empty-state"><span>🕯️</span><p>No hay aventureros registrados.</p></div>`;
        if (contadorPersonajes) contadorPersonajes.innerText = "0 héroes";
        return;
    }

    // Alimenta el selector desplegable lateral secundario
    llenarMenuPersonajes(lista);
    if (contadorPersonajes) contadorPersonajes.innerText = `${lista.length} héroe${lista.length === 1 ? "" : "s"}`;

    // Construcción limpia y de alto rendimiento mediante acumulación en memoria en un string único
    let htmlCards = "";
    lista.forEach((p) => {
        const claseNombre = NOMBRES_CLASES[p.id_clase] || 'Aventurero';

        htmlCards += `
            <div class="card-personaje" data-personaje-id="${p.id}">
                <div class="card-avatar-wrapper">
                    <div class="card-avatar">${claseNombre === 'Mago' ? '🧙' : '⚔️'}</div>
                </div>
                
                <div class="card-body-wrapper">
                    <h3 class="card-hero-name">${p.nombre || "Aventurero"}</h3>
                    <p class="card-hero-class">${claseNombre} · <span class="card-level-txt">Lv.${p.nivel ?? 1}</span></p>
                </div>
            </div>
        `;
    });

    // Inyección masiva optimizada provocando un único ciclo de repintado (Reflow) del árbol DOM
    contenedor.innerHTML = htmlCards;

    // Asigna controladores de clics individuales a las tarjetas inyectadas para permitir su selección reactiva
    document.querySelectorAll('.card-personaje').forEach(card => {
        card.addEventListener('click', () => {
            const idPersonaje = card.dataset.personajeId;
            if (menuPersonajes) menuPersonajes.value = idPersonaje; // Sincroniza el select desplegable secundario
            seleccionarPersonaje(idPersonaje); // Propaga las propiedades del héroe seleccionado
        });
    });

    escribirLog("Aventureros cargados correctamente.");
});

// Asigna un disparador manual al botón físico de recarga rápida de la barra de acciones
if (btnRecargar) {
    btnRecargar.addEventListener('click', pedirPersonajes);
}

/* ==========================================================================
   LOGICA ADICIONAL DE TABULADORES (Navegación por Pestañas con Atributos ARIA)
   ========================================================================== */
document.querySelectorAll('.tab-btn').forEach(boton => {
    boton.addEventListener('click', () => {
        // Limpieza de estados visuales activos y reinicio de atributos semánticos ARIA de accesibilidad
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Activa de forma exclusiva el botón de navegación sobre el que se efectuó el clic
        boton.classList.add('active');
        boton.setAttribute('aria-selected', 'true');

        // Localiza y visualiza el panel contenedor mapeado por el atributo 'data-tab'
        const tabId = boton.getAttribute('data-tab');
        const targetContent = document.getElementById(`tab-${tabId}`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    });
});

