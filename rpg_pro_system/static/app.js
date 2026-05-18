/* ==========================================================================
   XRPG GUILD MASTER — CLIENT LOGIC (static/app.js)
   ========================================================================== */

const socket = io();

/* ================== ELEMENTOS DEL DOM ================== */
const dot = document.getElementById('status-dot');
const text = document.getElementById('status-text');
const logBox = document.getElementById('log');

const contenedor = document.getElementById('contenedor-personajes');
const contadorPersonajes = document.getElementById('contador-personajes');
const btnRecargar = document.getElementById('btn-recargar');

const menuPersonajes = document.getElementById('menu-personajes');
const personajeSeleccionado = document.getElementById('personaje-seleccionado');
const selectedName = document.getElementById('selected-name');
const selectedLevel = document.getElementById('selected-level');
const selectedGold = document.getElementById('selected-gold');
const selectedHealth = document.getElementById('selected-health');
const selectedClass = document.getElementById('selected-class');
const selectedAvatar = document.querySelector('.selected-avatar');

const heroHud = document.getElementById('hero-hud');
const hudAvatar = document.getElementById('hud-avatar');
const hudName = document.getElementById('hud-name');
const hudLevel = document.getElementById('hud-level');
const hudGold = document.getElementById('hud-gold');
const hudHp = document.getElementById('hud-hp');

const skillTree = document.getElementById('skill-tree');
const badgeClase = document.getElementById('badge-clase');

const shopGrid = document.getElementById('shop-grid');
const badgeOro = document.getElementById('badge-oro');

const menuEnemigos = document.getElementById('menu-enemigos');
const btnIniciarCombate = document.getElementById('btn-iniciar-combate');
const combatArena = document.getElementById('combat-arena');
const combatActions = document.getElementById('combat-actions');
const combatLog = document.getElementById('combat-log');
const badgeTurno = document.getElementById('badge-turno');

const inventoryGrid = document.getElementById('inventory-grid');
const badgeItems = document.getElementById('badge-items');

/* ================== ESTADO DE LA APLICACIÓN ================== */
let personajesActuales = [];
let enemigosActuales = [];
let itemsActuales = [];
let personajeActivo = null;
let combateState = null;

const NOMBRES_CLASES = {
    1: 'Guerrero', 2: 'Mago', 3: 'Pícaro', 4: 'Paladín',
    5: 'Druida', 6: 'Bárbaro', 7: 'Clérigo', 8: 'Ranger',
    9: 'Bardo', 10: 'Brujo', 11: 'Hechicero', 12: 'Monje'
};

/* ================== FUNCIONES ÚTILES ================== */
/* ================== FUNCIONES ÚTILES ================== */
function escribirLog(mensaje) {
    if (!logBox) return;

    // 1. Creamos un nuevo párrafo para la línea del log
    const linea = document.createElement('p');
    linea.className = 'log-line'; // Por si quieres darle estilos en CSS (ej. un color grisáceo)
    linea.innerHTML = `<span class="log-prompt">&gt;</span> ${mensaje}`;

    // 2. Lo añadimos al contenedor en lugar de machacar todo
    logBox.appendChild(linea);

    // 3. Autoscroll: Mueve el scroll hacia abajo automáticamente para ver la última acción
    logBox.scrollTop = logBox.scrollHeight;
}

function mostrarToast(mensaje, tipo = 'error') {
    document.querySelectorAll('.toast').forEach(t => t.remove());
    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    toast.innerText = mensaje;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function pedirPersonajes() {
    escribirLog("Solicitando aventureros al servidor...");
    socket.emit('obtener_personajes');
}

function getVidaMax(p) {
    return Number(p.vida_max || p.vida_maxima || 100);
}

function rand(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/* ================== NAVEGACIÓN (TABS) ================== */
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const tabContent = document.getElementById('tab-' + btn.dataset.tab);
        if (tabContent) tabContent.classList.add('active');
    });
});

const btnIrCombate = document.getElementById('btn-ir-combate');
if (btnIrCombate) {
    btnIrCombate.addEventListener('click', () => {
        const tabCombate = document.querySelector('[data-tab="combate"]');
        if (tabCombate) tabCombate.click();
        const tabsPanel = document.querySelector('.tabs-panel');
        if (tabsPanel) tabsPanel.scrollIntoView({ behavior: 'smooth' });
    });
}

/* ================== GESTIÓN DE PERSONAJES ================== */
function llenarMenuPersonajes(lista) {
    if (!menuPersonajes) return;
    menuPersonajes.innerHTML = '<option value="">Selecciona un aventurero...</option>';
    lista.forEach((p) => {
        const option = document.createElement('option');
        option.value = p.id;
        option.textContent = `${p.nombre || "Aventurero"} — Nivel ${p.nivel ?? 1}`;
        menuPersonajes.appendChild(option);
    });
}

function seleccionarPersonaje(idPersonaje) {
    const personaje = personajesActuales.find(p => String(p.id) === String(idPersonaje));

    document.querySelectorAll('.card-personaje').forEach(card => card.classList.remove('selected'));

    // MEJORA: Limpieza profunda del DOM cuando no hay ningún personaje seleccionado
    if (!personaje) {
        if (personajeSeleccionado) personajeSeleccionado.classList.add('hidden');
        if (heroHud) heroHud.classList.add('hidden');
        if (skillTree) skillTree.innerHTML = `<div class="empty-state"><span>🪄</span><p>Selecciona un personaje para ver su progreso.</p></div>`;
        if (inventoryGrid) inventoryGrid.innerHTML = `<div class="empty-state"><span>🎒</span><p>Mochila vacía.</p></div>`;
        if (badgeOro) badgeOro.innerText = `💰 0 oro`;
        if (badgeItems) badgeItems.innerText = `0 objetos`;
        personajeActivo = null;
        escribirLog("Ningún personaje seleccionado.");
        return;
    }

    personajeActivo = personaje;
    const card = document.querySelector(`[data-personaje-id="${personaje.id}"]`);
    if (card) card.classList.add('selected');

    const vida = personaje.vida_actual ?? 0;
    const vidaMax = getVidaMax(personaje);
    const inicial = (personaje.nombre || "?").charAt(0).toUpperCase();
    const claseNombre = NOMBRES_CLASES[personaje.id_clase] || 'Aventurero';

    if (selectedAvatar) selectedAvatar.innerText = inicial;
    if (selectedName) selectedName.innerText = personaje.nombre || "Aventurero";
    if (selectedLevel) selectedLevel.innerText = `Nivel: ${personaje.nivel ?? 1}`;
    if (selectedGold) selectedGold.innerText = `Oro: ${personaje.oro ?? 0}`;
    if (selectedHealth) selectedHealth.innerText = `Vida: ${vida}/${vidaMax}`;
    if (selectedClass) selectedClass.innerText = `Clase: ${claseNombre}`;
    if (personajeSeleccionado) personajeSeleccionado.classList.remove('hidden');

    if (hudAvatar) hudAvatar.innerText = inicial;
    if (hudName) hudName.innerText = personaje.nombre || "Aventurero";
    if (hudLevel) hudLevel.innerText = personaje.nivel ?? 1;
    if (hudGold) hudGold.innerText = personaje.oro ?? 0;
    if (hudHp) hudHp.innerText = `${vida}/${vidaMax}`;
    if (heroHud) heroHud.classList.remove('hidden');

    cargarHabilidades(personaje.id_clase, claseNombre);
    cargarInventario(personaje.id);
    if (badgeOro) badgeOro.innerText = `💰 ${personaje.oro ?? 0} oro`;

    escribirLog(`Personaje seleccionado: ${personaje.nombre}.`);
}

if (menuPersonajes) {
    menuPersonajes.addEventListener('change', () => seleccionarPersonaje(menuPersonajes.value));
}

/* ================== ÁRBOL DE HABILIDADES ================== */
async function cargarHabilidades(claseId, claseNombre) {
    if (!skillTree) return;
    badgeClase.innerText = claseNombre || 'Sin clase';
    skillTree.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando habilidades...</p></div>`;

    if (!personajeActivo) {
        skillTree.innerHTML = `<div class="empty-state"><span>🪄</span><p>Selecciona un personaje para ver su progreso.</p></div>`;
        return;
    }

    try {
        const res = await fetch(`/api/personajes/arbol-habilidades?clase_id=${claseId}&personaje_id=${personajeActivo.id}`);
        const habilidades = await res.json();

        if (!Array.isArray(habilidades) || habilidades.length === 0) {
            skillTree.innerHTML = `<div class="empty-state"><span>📭</span><p>Sin habilidades para esta clase.</p></div>`;
            return;
        }

        renderArbolHabilidades(habilidades);
    } catch (err) {
        skillTree.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando habilidades.</p></div>`;
    }
}

function renderArbolHabilidades(habilidades) {
    const orden = { 'pasiva': 0, 'activa': 1, 'ultimate': 2 };
    habilidades.sort((a, b) => (orden[a.tipo] ?? 1) - (orden[b.tipo] ?? 1));

    skillTree.innerHTML = habilidades.map((h, idx) => {
        const tipo = h.tipo || 'activa';

        let icono = '✨';
        if (tipo === 'pasiva') icono = '🛡️';
        if (tipo === 'ultimate') icono = '🔥';

        const manaTexto = h.costo_mana > 0 ? `💧 <b>${h.costo_mana} MP</b>` : '✨ <b>Pasiva</b>';
        const danoTexto = h.dano_base > 0 ? `⚔️ <b>${h.dano_base} Poder</b>` : '📜 <b>Efecto</b>';

        const nivelActual = h.nivel_actual ?? 0;
        const nivelMaximo = h.nivel_maximo ?? 1;
        const esMaximo = nivelActual >= nivelMaximo;

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
    }).join('');

    skillTree.querySelectorAll('.btn-mejorar-habilidad').forEach(btn => {
        btn.addEventListener('click', () => {
            mejorarHabilidad(btn.dataset.skillId);
        });
    });
}

async function mejorarHabilidad(idHabilidad) {
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

        if (!resultado.ok) {
            if (resultado.requisites_faltantes?.length) {
                const lista = resultado.requisites_faltantes
                    .map(r => `${r.nombre} (necesitas Lv ${r.nivel_necesario}, tienes Lv ${r.nivel_actual})`)
                    .join(' | ');
                escribirLog(`Requisitos faltantes: ${lista}`);
                mostrarToast(`Requisitos: ${lista}`, 'warn');
            } else {
                escribirLog(resultado.mensaje);
                mostrarToast(resultado.mensaje, 'warn');
            }
            return;
        }

        const hab = resultado.habilidad;
        const nodo = document.querySelector(`[data-skill-id="${hab.id}"]`);
        if (nodo) {
            let badge = nodo.querySelector('.skill-level-badge');
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'skill-level-badge';
                nodo.prepend(badge);
            }
            badge.innerText = `Lv ${hab.nivel_actual}/${hab.nivel_maximo}`;
            if (hab.nivel_actual >= hab.nivel_maximo) {
                nodo.classList.add('skill-maxed');
                const btn = nodo.querySelector('.btn-mejorar-habilidad');
                if (btn) { btn.disabled = true; btn.innerText = '✅ Máximo Nivel'; }
            }
        }

        escribirLog(resultado.mensaje);
        mostrarToast(resultado.mensaje, 'ok');

    } catch (err) {
        escribirLog("Error de red al mejorar la habilidad.");
        console.error(err);
    }
}

/* ================== TIENDA COMERCIAL ================== */
async function cargarTienda(rareza = '') {
    if (!shopGrid) return;
    shopGrid.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando objetos...</p></div>`;
    try {
        const url = rareza ? `/api/items/?rareza=${encodeURIComponent(rareza)}` : '/api/items/';
        const res = await fetch(url);
        itemsActuales = await res.json();

        const kpiItems = document.getElementById('kpi-items');
        if (kpiItems) kpiItems.innerText = itemsActuales.length;

        if (!itemsActuales.length) {
            shopGrid.innerHTML = `<div class="empty-state"><span>📦</span><p>Sin objetos disponibles.</p></div>`;
            return;
        }

        shopGrid.innerHTML = itemsActuales.map(it => {
            const rar = (it.rareza || 'Común').toLowerCase();
            const stats = it.stats || {};
            const statsHtml = Object.entries(stats)
                .filter(([_, v]) => v && Number(v) !== 0)
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
        }).join('');

        shopGrid.querySelectorAll('.btn-comprar-item').forEach(btn => {
            btn.addEventListener('click', () => comprarItem(Number(btn.dataset.itemId)));
        });

    } catch (err) {
        shopGrid.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando la tienda.</p></div>`;
    }
}

// CORREGIDO: Transformada en función asíncrona para guardar compras reales en la base de datos de Flask y actualizar inventario
async function comprarItem(itemId) {
    if (!personajeActivo) {
        escribirLog("Selecciona un héroe antes de comprar.");
        return;
    }
    const item = itemsActuales.find(i => i.id === itemId);
    if (!item) return;

    if ((personajeActivo.oro ?? 0) < item.precio) {
        escribirLog(`No tienes oro suficiente para ${item.nombre}.`);
        mostrarToast("No tienes oro suficiente", "warn");
        return;
    }

    try {
        const res = await fetch('/api/tienda/comprar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id_personaje: personajeActivo.id,
                id_item: itemId
            })
        });

        const resultado = await res.json();

        if (!resultado.ok) {
            escribirLog(resultado.mensaje);
            mostrarToast(resultado.mensaje, 'warn');
            return;
        }

        // Sincronizamos el estado local con los datos oficiales del servidor backend
        personajeActivo.oro = resultado.oro_restante;

        const refLista = personajesActuales.find(p => p.id === personajeActivo.id);
        if (refLista) refLista.oro = personajeActivo.oro;

        if (hudGold) hudGold.innerText = personajeActivo.oro;
        if (selectedGold) selectedGold.innerText = `Oro: ${personajeActivo.oro}`;
        if (badgeOro) badgeOro.innerText = `💰 ${personajeActivo.oro} oro`;

        escribirLog(`¡Compra confirmada! Has adquirido ${item.nombre} por ${item.precio} de oro.`);
        mostrarToast(`Comprado: ${item.nombre}`, 'ok');

        // Refrescar inventario y cards laterales de inmediato
        cargarInventario(personajeActivo.id);
        pedirPersonajes();

    } catch (err) {
        escribirLog("Error de red al realizar la compra.");
        console.error(err);
    }
}

document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        cargarTienda(chip.dataset.rareza);
    });
});

/* ================== INVENTARIO MOCHILA ================== */
async function cargarInventario(personajeId) {
    if (!inventoryGrid) return;
    inventoryGrid.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando mochila...</p></div>`;
    try {
        const res = await fetch(`/api/inventario/?id=${personajeId}`);
        const items = await res.json();
        if (badgeItems) badgeItems.innerText = `${items.length} objeto${items.length === 1 ? '' : 's'}`;

        if (!items.length) {
            inventoryGrid.innerHTML = `<div class="empty-state"><span>🎒</span><p>Mochila vacía.</p></div>`;
            return;
        }

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

/* ================== ARENA DE COMBATE SIMULADO ================== */
async function cargarEnemigos() {
    if (!menuEnemigos) return;
    try {
        const res = await fetch('/api/enemigos');
        enemigosActuales = await res.json();

        const kpiEnemigos = document.getElementById('kpi-enemigos');
        if (kpiEnemigos) kpiEnemigos.innerText = enemigosActuales.length;

        menuEnemigos.innerHTML = '<option value="">Selecciona un enemigo...</option>' +
            enemigosActuales.map(e =>
                `<option value="${e.id}">${e.nombre} — Lv ${e.nivel} (${e.vida_max} HP)</option>`
            ).join('');
    } catch {
        menuEnemigos.innerHTML = '<option value="">Error cargando enemigos</option>';
    }
}

if (btnIniciarCombate) {
    btnIniciarCombate.addEventListener('click', () => {
        if (!personajeActivo) {
            escribirLog("Elige un héroe antes de combatir.");
            return;
        }
        const enemigo = enemigosActuales.find(e => String(e.id) === String(menuEnemigos.value));

        if (!enemigo) {
            escribirLog("Elige un enemigo válido.");
            return;
        }

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
            defendiendo: false
        };

        document.getElementById('hero-avatar').innerText = (personajeActivo.nombre || '?').charAt(0).toUpperCase();
        document.getElementById('hero-name').innerText = personajeActivo.nombre;
        document.getElementById('enemy-avatar').innerText = '👹';
        document.getElementById('enemy-name').innerText = enemigo.nombre;

        actualizarBarrasCombate();
        if (combatArena) combatArena.classList.remove('hidden');
        if (combatActions) combatActions.classList.remove('hidden');
        if (combatLog) combatLog.innerHTML = `<p>&gt; ¡${personajeActivo.nombre} desafía a ${enemigo.nombre}!</p>`;
        if (badgeTurno) badgeTurno.innerText = `Turno ${combateState.turno}`;
    });
}

function actualizarBarrasCombate() {
    if (!combateState) return;
    const h = combateState.heroe;
    const e = combateState.enemigo;

    document.getElementById('hero-hp-fill').style.width = `${Math.max(0, h.hp / h.hpMax * 100)}%`;
    document.getElementById('hero-hp-text').innerText = `${Math.max(0, h.hp)}/${h.hpMax}`;
    document.getElementById('enemy-hp-fill').style.width = `${Math.max(0, e.hp / e.hpMax * 100)}%`;
    document.getElementById('enemy-hp-text').innerText = `${Math.max(0, e.hp)}/${e.hpMax}`;
}

function logCombate(msg) {
    if (!combatLog) return;
    const p = document.createElement('p');
    p.innerHTML = '&gt; ' + msg;
    combatLog.appendChild(p);
    combatLog.scrollTop = combatLog.scrollHeight;
}

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
    }).catch(() => {});
}

function turnoEnemigo() {
    if (!combateState) return;
    if (combateState.enemigo.hp <= 0) return finalizarCombate('victoria');

    const danoBase = combateState.enemigo.dano;
    const dano = combateState.defendiendo ? Math.max(1, Math.floor(danoBase / 2)) : danoBase + rand(-2, 2);
    combateState.heroe.hp -= dano;

    logCombate(`👹 ${combateState.enemigo.nombre} te golpea por <b>${dano}</b> de daño${combateState.defendiendo ? ' (mitigado)' : ''}.`);
    combateState.defendiendo = false;
    actualizarBarrasCombate();

    if (combateState.heroe.hp <= 0) return finalizarCombate('derrota');
    combateState.turno++;
    if (badgeTurno) badgeTurno.innerText = `Turno ${combateState.turno}`;
}

if (combatActions) {
    combatActions.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!combateState) return;
            const accion = btn.dataset.accion;

            if (accion === 'huir') {
                logCombate(`🏃 Huyes del combate.`);
                registrarAccionBackend('huir', 0, 0, 'huida');
                finalizarCombate('huida');
                return;
            }

            let danoInfligido = 0;
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

            if (combateState.enemigo.hp <= 0) {
                registrarAccionBackend(accion, danoInfligido, 0, 'victoria');
                return finalizarCombate('victoria');
            }
            registrarAccionBackend(accion, danoInfligido, 0, 'continua');
            setTimeout(turnoEnemigo, 600);
        });
    });
}

function finalizarCombate(resultado) {
    if (combatActions) combatActions.classList.add('hidden');
    if (resultado === 'victoria') {
        logCombate(`🏆 <b>¡Victoria!</b> Has derrotado a ${combateState.enemigo.nombre}.`);
    } else if (resultado === 'derrota') {
        logCombate(`💀 <b>Has caído</b> en combate...`);
    } else {
        logCombate(`Combate finalizado.`);
    }
    combateState = null;
}

/* ================== SUBIR DE NIVEL GLOBAL ================== */
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

        if (!resultado.ok) {
            escribirLog(resultado.mensaje);
            mostrarToast(resultado.mensaje, 'warn');
            return;
        }

        const datos = resultado.personaje;
        personajeActivo.nivel        = datos.nivel_actual;
        personajeActivo.vida_max     = datos.vida_max;
        personajeActivo.vida_actual  = datos.vida_actual;
        personajeActivo.fuerza       = datos.fuerza;
        personajeActivo.agilidad     = datos.agilidad;
        personajeActivo.inteligencia = datos.inteligencia;
        personajeActivo.mana_max     = datos.mana_max || personajeActivo.mana_max;
        personajeActivo.mana_actual  = datos.mana_actual || personajeActivo.mana_actual;

        if (hudLevel) hudLevel.innerText             = datos.nivel_actual;
        if (hudHp) hudHp.innerText                   = `${datos.vida_actual}/${datos.vida_max}`;
        if (selectedLevel) selectedLevel.innerText   = `Nivel: ${datos.nivel_actual}`;
        if (selectedHealth) selectedHealth.innerText = `Vida: ${datos.vida_actual}/${datos.vida_max}`;

        const expInfo = document.getElementById('exp-info');
        if (expInfo) expInfo.innerText = `EXP: ${datos.exp_restante} / ${datos.exp_para_siguiente_nivel}`;

        escribirLog(resultado.mensaje);
        mostrarToast(resultado.mensaje, 'ok');
        pedirPersonajes();

    } catch (err) {
        escribirLog("Error de red al subir nivel.");
        console.error(err);
    }
}

const btnSubirNivel = document.getElementById('btn-subir-nivel');
if (btnSubirNivel) {
    btnSubirNivel.addEventListener('click', subirNivelPersonaje);
}

/* ================== RECEPTORES SOCKET.IO ================== */
socket.on('connect', () => {
    if (dot) dot.className = 'dot connected';
    if (text) text.innerText = 'Conectado';
    escribirLog("Conectado con éxito al servidor.");
    pedirPersonajes();
    cargarTienda();
    cargarEnemigos();
});

socket.on('disconnect', () => {
    if (dot) dot.className = 'dot disconnected';
    if (text) text.innerText = 'Desconectado';
    escribirLog("Se perdió la conexión con el servidor.");
});

socket.on('status', (data) => escribirLog(data.msg));

socket.on('personajes', (lista) => {
    personajesActuales = lista || [];
    if (!contenedor) return;

    const kpiHeroes = document.getElementById('kpi-heroes');
    if (kpiHeroes) kpiHeroes.innerText = personajesActuales.length;

    if (!lista || lista.length === 0) {
        if (menuPersonajes) menuPersonajes.innerHTML = '<option value="">No hay personajes disponibles</option>';
        if (personajeSeleccionado) personajeSeleccionado.classList.add('hidden');
        contenedor.innerHTML = `<div class="empty-state"><span>🕯️</span><p>No hay aventureros registrados.</p></div>`;
        if (contadorPersonajes) contadorPersonajes.innerText = "0 héroes";
        return;
    }

    llenarMenuPersonajes(lista);
    if (contadorPersonajes) contadorPersonajes.innerText = `${lista.length} héroe${lista.length === 1 ? "" : "s"}`;

    // MEJORA: Construcción asíncrona limpia en un único string antes de inyectar al DOM
    let htmlCards = "";
    lista.forEach((p) => {
        const vida = Number(p.vida_actual || 0);
        const vidaMax = getVidaMax(p);
        const porcentaje = Math.max(0, Math.min(100, (vida / vidaMax) * 100));
        const claseNombre = NOMBRES_CLASES[p.id_clase] || 'Aventurero';

        htmlCards += `
            <div class="card-personaje" data-personaje-id="${p.id}">
                <div class="card-top">
                    <div class="avatar">${(p.nombre || "?").charAt(0).toUpperCase()}</div>
                    <div>
                        <h3>${p.nombre || "Aventurero"}</h3>
                        <p>${claseNombre}</p>
                    </div>
                </div>
                <div class="stats-grid">
                    <div><span>Nivel</span><strong>${p.nivel ?? 1}</strong></div>
                    <div><span>Oro</span><strong>${p.oro ?? 0}</strong></div>
                </div>
                <div class="health-block">
                    <div class="health-info"><span>Vida</span><strong>${vida}/${vidaMax}</strong></div>
                    <div class="health-bar"><div style="width: ${porcentaje}%"></div></div>
                </div>
            </div>
        `;
    });

    contenedor.innerHTML = htmlCards;

    document.querySelectorAll('.card-personaje').forEach(card => {
        card.addEventListener('click', () => {
            const idPersonaje = card.dataset.personajeId;
            if (menuPersonajes) menuPersonajes.value = idPersonaje;
            seleccionarPersonaje(idPersonaje);
        });
    });

    escribirLog("Aventureros cargados correctamente.");
});

if (btnRecargar) {
    btnRecargar.addEventListener('click', pedirPersonajes);
}

// Lógica para alternar entre pestañas
document.querySelectorAll('.tab-btn').forEach(boton => {
    boton.addEventListener('click', () => {
        // Quitar la clase active de todos los botones y ocultar contenidos
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Activar la pestaña clicada
        boton.classList.add('active');
        boton.setAttribute('aria-selected', 'true');

        const tabId = boton.getAttribute('data-tab');
        const targetContent = document.getElementById(`tab-${tabId}`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    });
});

