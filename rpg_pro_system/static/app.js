/* ==========================================================================
   XRPG GUILD MASTER — CLIENT LOGIC (static/app.js)
   ========================================================================== */

const socket = typeof io !== 'undefined' ? io() : null; // Prevención de errores si falla CDN

/* ==========================================================================
   OBJETO DOM (Centralización y Caché de Selectores)
   ========================================================================== */
const DOM = {
    // Red y Log
    dot: document.getElementById('status-dot'),
    text: document.getElementById('status-text'),
    logBox: document.getElementById('log'),

    // Contenedores Principales
    contenedorPersonajes: document.getElementById('contenedor-personajes'),
    contadorPersonajes: document.getElementById('contador-personajes'),
    menuPersonajes: document.getElementById('menu-personajes'),

    // Panel de Selección
    personajeSeleccionado: document.getElementById('personaje-seleccionado'),
    selectedName: document.getElementById('selected-name'),
    selectedLevel: document.getElementById('selected-level'),
    selectedGold: document.getElementById('selected-gold'),
    selectedHealth: document.getElementById('selected-health'),
    selectedClass: document.getElementById('selected-class'),
    selectedAvatar: document.querySelector('.selected-avatar'),
    expInfo: document.getElementById('exp-info'),

    // HUD Superior
    heroHud: document.getElementById('hero-hud'),
    hudAvatar: document.getElementById('hud-avatar'),
    hudName: document.getElementById('hud-name'),
    hudLevel: document.getElementById('hud-level'),
    hudGold: document.getElementById('hud-gold'),
    hudHp: document.getElementById('hud-hp'),

    // Árbol de Habilidades y Tienda
    skillTree: document.getElementById('skill-tree'),
    badgeClase: document.getElementById('badge-clase'),
    shopGrid: document.getElementById('shop-grid'),
    badgeOro: document.getElementById('badge-oro'),

    // Arena de Combate
    menuEnemigos: document.getElementById('menu-enemigos'),
    combatArena: document.getElementById('combat-arena'),
    combatActions: document.getElementById('combat-actions'),
    combatLog: document.getElementById('combat-log'),
    badgeTurno: document.getElementById('badge-turno'),

    // Inventario
    inventoryGrid: document.getElementById('inventory-grid'),
    badgeItems: document.getElementById('badge-items'),

    // Estadísticas
    statsEmpty: document.getElementById('stats-empty-state'),
    statsHud: document.getElementById('stats-hud-wrapper'),

    // Botones
    btnRecargar: document.getElementById('btn-recargar'),
    btnIniciarCombate: document.getElementById('btn-iniciar-combate'),
    btnIrCombate: document.getElementById('btn-ir-combate'),
    btnSubirNivel: document.getElementById('btn-subir-nivel'),

    // KPIs
    kpiHeroes: document.getElementById('kpi-heroes'),
    kpiEnemigos: document.getElementById('kpi-enemigos'),
    kpiItems: document.getElementById('kpi-items')
};

/* ==========================================================================
   ESTADO GLOBAL CONSTANTES
   ========================================================================== */
const STATE = {
    personajes: [],
    enemigos: [],
    items: [],
    personajeActivo: null,
    combate: null
};

const NOMBRES_CLASES = {
    1: 'Guerrero', 2: 'Mago', 3: 'Pícaro', 4: 'Paladín',
    5: 'Druida', 6: 'Bárbaro', 7: 'Clérigo', 8: 'Ranger',
    9: 'Bardo', 10: 'Brujo', 11: 'Hechicero', 12: 'Monje'
};

/* ==========================================================================
   FUNCIONES ÚTILES Y AUXILIARES
   ========================================================================== */
function escribirLog(mensaje) {
    if (!DOM.logBox) return;
    const linea = document.createElement('p');
    linea.className = 'log-entry';
    linea.innerHTML = `<span class="log-prompt">&gt;</span> ${mensaje}`;
    DOM.logBox.appendChild(linea);
    DOM.logBox.scrollTop = DOM.logBox.scrollHeight;
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
    if(socket) socket.emit('obtener_personajes');
}

function getVidaMax(p) { return Number(p.vida_max || p.vida_maxima || 100); }
function rand(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }

/* ==========================================================================
   SISTEMA DE PESTAÑAS (TABS)
   ========================================================================== */
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');

        const tabContent = document.getElementById('tab-' + btn.dataset.tab);
        if (tabContent) tabContent.classList.add('active');
    });
});

if (DOM.btnIrCombate) {
    DOM.btnIrCombate.addEventListener('click', () => {
        const tabCombate = document.querySelector('[data-tab="combate"]');
        if (tabCombate) tabCombate.click();
        const tabsPanel = document.querySelector('.tabs-panel');
        if (tabsPanel) tabsPanel.scrollIntoView({ behavior: 'smooth' });
    });
}

/* ==========================================================================
   GESTIÓN DE PERSONAJES
   ========================================================================== */
async function cargarPanelEstadisticas(idPersonaje) {
    try {
        const response = await fetch(`/api/personajes/${idPersonaje}/estadisticas`);
        if (!response.ok) throw new Error("Error obteniendo estadísticas.");
        const data = await response.json();

        if (!data) return;

        if (DOM.selectedHealth) DOM.selectedHealth.innerText = `Vida: ${data.vida_actual}/${data.vida_max}`;
        if (DOM.hudHp) DOM.hudHp.innerText = `${data.vida_actual}/${data.vida_max}`;

        if (STATE.personajeActivo) {
            Object.assign(STATE.personajeActivo, {
                vida_actual: data.vida_actual,
                vida_max: data.vida_max,
                fuerza: data.fuerza,
                agilidad: data.agilidad,
                inteligencia: data.inteligencia
            });
        }

        if (DOM.statsEmpty) DOM.statsEmpty.classList.add('hidden');
        if (DOM.statsHud) DOM.statsHud.classList.remove('hidden');

        // Sincronización Barras y Stats
        const els = {
            hpText: document.getElementById('real-hp-text'),
            hpFill: document.getElementById('real-hp-fill'),
            resName: document.getElementById('real-resource-name'),
            mpText: document.getElementById('real-mp-text'),
            mpFill: document.getElementById('real-mp-fill'),
            str: document.getElementById('stat-fuerza'),
            agi: document.getElementById('stat-agilidad'),
            int: document.getElementById('stat-inteligencia')
        };

        if (els.hpText) els.hpText.innerText = `${data.vida_actual} / ${data.vida_max}`;
        if (els.hpFill) els.hpFill.style.width = `${(data.vida_actual / data.vida_max) * 100}%`;

        const tipoRecurso = data.recurso_primario || 'Maná';
        if (els.resName) els.resName.innerText = `✨ ${tipoRecurso.toUpperCase()}`;
        if (els.mpText) els.mpText.innerText = `${data.mana_actual} / ${data.mana_max}`;
        if (els.mpFill) els.mpFill.style.width = `${data.mana_max > 0 ? (data.mana_actual / data.mana_max) * 100 : 0}%`;

        if (els.str) els.str.innerText = data.fuerza ?? 10;
        if (els.agi) els.agi.innerText = data.agilidad ?? 10;
        if (els.int) els.int.innerText = data.inteligencia ?? 10;

        escribirLog(`Atributos reales sincronizados.`);
    } catch (error) {
        console.error("❌ Error en estadísticas:", error);
    }
}

function llenarMenuPersonajes(lista) {
    if (!DOM.menuPersonajes) return;
    DOM.menuPersonajes.innerHTML = '<option value="">Selecciona un aventurero...</option>' +
        lista.map(p => `<option value="${p.id}">${p.nombre || "Aventurero"} — Nivel ${p.nivel ?? 1}</option>`).join('');
}

function seleccionarPersonaje(idPersonaje) {
    const personaje = STATE.personajes.find(p => String(p.id) === String(idPersonaje));
    document.querySelectorAll('.card-personaje').forEach(card => card.classList.remove('selected'));

    if (!personaje) {
        [DOM.personajeSeleccionado, DOM.heroHud, DOM.statsHud].forEach(el => el && el.classList.add('hidden'));
        if (DOM.statsEmpty) DOM.statsEmpty.classList.remove('hidden');
        if (DOM.skillTree) DOM.skillTree.innerHTML = `<div class="empty-state"><span>🪄</span><p>Selecciona un personaje.</p></div>`;
        if (DOM.inventoryGrid) DOM.inventoryGrid.innerHTML = `<div class="empty-state"><span>🎒</span><p>Mochila vacía.</p></div>`;
        if (DOM.badgeOro) DOM.badgeOro.innerText = `💰 0 oro`;
        if (DOM.badgeItems) DOM.badgeItems.innerText = `0 objetos`;
        STATE.personajeActivo = null;
        return;
    }

    STATE.personajeActivo = personaje;

    const card = document.querySelector(`[data-personaje-id="${personaje.id}"]`);
    if (card) card.classList.add('selected');

    const inicial = (personaje.nombre || "?").charAt(0).toUpperCase();
    const claseNombre = NOMBRES_CLASES[personaje.id_clase] || 'Aventurero';

    if (DOM.selectedAvatar) DOM.selectedAvatar.innerText = inicial;
    if (DOM.selectedName) DOM.selectedName.innerText = personaje.nombre || "Aventurero";
    if (DOM.selectedLevel) DOM.selectedLevel.innerText = `Nivel: ${personaje.nivel ?? 1}`;
    if (DOM.selectedGold) DOM.selectedGold.innerText = `Oro: ${personaje.oro ?? 0}`;
    if (DOM.selectedClass) DOM.selectedClass.innerText = `Clase: ${claseNombre}`;
    if (DOM.personajeSeleccionado) DOM.personajeSeleccionado.classList.remove('hidden');

    if (DOM.hudAvatar) DOM.hudAvatar.innerText = inicial;
    if (DOM.hudName) DOM.hudName.innerText = personaje.nombre || "Aventurero";
    if (DOM.hudLevel) DOM.hudLevel.innerText = personaje.nivel ?? 1;
    if (DOM.hudGold) DOM.hudGold.innerText = personaje.oro ?? 0;
    if (DOM.heroHud) DOM.heroHud.classList.remove('hidden');

    if (DOM.selectedHealth) DOM.selectedHealth.innerText = `Vida: ...`;
    if (DOM.hudHp) DOM.hudHp.innerText = `...`;

    cargarHabilidades(personaje.id_clase, claseNombre);
    cargarInventario(personaje.id);
    cargarPanelEstadisticas(personaje.id);

    if (DOM.badgeOro) DOM.badgeOro.innerText = `💰 ${personaje.oro ?? 0} oro`;
    escribirLog(`Personaje seleccionado: ${personaje.nombre}.`);
}

if (DOM.menuPersonajes) {
    DOM.menuPersonajes.addEventListener('change', () => seleccionarPersonaje(DOM.menuPersonajes.value));
}

// OPTIMIZACIÓN: Delegación de Eventos para Tarjetas de Personajes
if(DOM.contenedorPersonajes) {
    DOM.contenedorPersonajes.addEventListener('click', (e) => {
        const card = e.target.closest('.card-personaje');
        if(!card) return;
        const idPersonaje = card.dataset.personajeId;
        if (DOM.menuPersonajes) DOM.menuPersonajes.value = idPersonaje;
        seleccionarPersonaje(idPersonaje);
    });
}

/* ==========================================================================
   ÁRBOL DE HABILIDADES Y TIENDA (Optimizados con Event Delegation)
   ========================================================================== */
async function cargarHabilidades(claseId, claseNombre) {
    if (!DOM.skillTree) return;
    if (DOM.badgeClase) DOM.badgeClase.innerText = claseNombre || 'Sin clase';
    DOM.skillTree.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando habilidades...</p></div>`;

    if (!STATE.personajeActivo) {
        DOM.skillTree.innerHTML = `<div class="empty-state"><span>🪄</span><p>Selecciona un personaje.</p></div>`;
        return;
    }

    try {
        const res = await fetch(`/api/personajes/arbol-habilidades?clase_id=${claseId}&personaje_id=${STATE.personajeActivo.id}`);
        const habilidades = await res.json();

        if (!Array.isArray(habilidades) || habilidades.length === 0) {
            DOM.skillTree.innerHTML = `<div class="empty-state"><span>📭</span><p>Sin habilidades para esta clase.</p></div>`;
            return;
        }
        renderArbolHabilidades(habilidades);
    } catch (err) {
        DOM.skillTree.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando habilidades.</p></div>`;
    }
}

function renderArbolHabilidades(habilidades) {
    const orden = { 'pasiva': 0, 'activa': 1, 'ultimate': 2 };
    habilidades.sort((a, b) => (orden[a.tipo] ?? 1) - (orden[b.tipo] ?? 1));

    DOM.skillTree.innerHTML = habilidades.map((h, idx) => {
        const tipo = h.tipo || 'activa';
        const icono = tipo === 'pasiva' ? '🛡️' : tipo === 'ultimate' ? '🔥' : '✨';
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
                <p class="skill-desc">${h.descripcion || 'Sin descripción.'}</p>
                <div class="skill-stats">
                    <div class="stat-box"><span>Coste</span>${manaTexto}</div>
                    <div class="stat-box"><span>Poder Base</span>${danoTexto}</div>
                    <div class="stat-box"><span>Categoría</span><b class="type-txt">${tipo.toUpperCase()}</b></div>
                </div>
                <button class="btn-mejorar-habilidad" data-skill-id="${h.id}" ${esMaximo ? 'disabled' : ''}>
                    ${esMaximo ? '✅ Máximo Nivel' : '⬆️ Mejorar Habilidad'}
                </button>
            </div>
            ${arrow}
        `;
    }).join('');
}

// OPTIMIZACIÓN: Delegación de Eventos Árbol Habilidades
if(DOM.skillTree) {
    DOM.skillTree.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-mejorar-habilidad');
        if(btn && !btn.disabled) mejorarHabilidad(btn.dataset.skillId);
    });
}

async function mejorarHabilidad(idHabilidad) {
    if (!STATE.personajeActivo) return;
    try {
        const res = await fetch('/api/habilidad/subir-nivel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_personaje: STATE.personajeActivo.id, id_habilidad: idHabilidad })
        });
        const resultado = await res.json();

        if (!resultado.ok) {
            const msj = resultado.requisites_faltantes?.length
                ? `Requisitos: ` + resultado.requisites_faltantes.map(r => `${r.nombre} (Lv ${r.nivel_necesario})`).join(' | ')
                : resultado.mensaje;
            escribirLog(msj);
            mostrarToast(msj, 'warn');
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
        console.error(err);
    }
}

async function cargarTienda(rareza = '') {
    if (!DOM.shopGrid) return;
    DOM.shopGrid.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando objetos...</p></div>`;

    try {
        const url = rareza ? `/api/items/?rareza=${encodeURIComponent(rareza)}` : '/api/items/';
        const res = await fetch(url);
        STATE.items = await res.json();

        if (DOM.kpiItems) DOM.kpiItems.innerText = STATE.items.length;

        if (!STATE.items.length) {
            DOM.shopGrid.innerHTML = `<div class="empty-state"><span>📦</span><p>Sin objetos disponibles.</p></div>`;
            return;
        }

        DOM.shopGrid.innerHTML = STATE.items.map(it => {
            const rar = (it.rareza || 'Común').toLowerCase();
            const statsHtml = Object.entries(it.stats || {})
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
    } catch (err) {
        DOM.shopGrid.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando la tienda.</p></div>`;
    }
}

// OPTIMIZACIÓN: Delegación de Eventos Tienda
if(DOM.shopGrid) {
    DOM.shopGrid.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-comprar-item');
        if(btn) comprarItem(Number(btn.dataset.itemId));
    });
}

async function comprarItem(itemId) {
    if (!STATE.personajeActivo) {
        mostrarToast("Selecciona un héroe antes de comprar.", "warn");
        return;
    }
    const item = STATE.items.find(i => i.id === itemId);
    if (!item || (STATE.personajeActivo.oro ?? 0) < item.precio) {
        mostrarToast("No tienes oro suficiente", "warn");
        return;
    }

    try {
        const res = await fetch('/api/tienda/comprar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_personaje: STATE.personajeActivo.id, id_item: itemId })
        });
        const resultado = await res.json();

        if (!resultado.ok) {
            mostrarToast(resultado.mensaje, 'warn');
            return;
        }

        STATE.personajeActivo.oro = resultado.oro_restante;
        const refLista = STATE.personajes.find(p => p.id === STATE.personajeActivo.id);
        if (refLista) refLista.oro = STATE.personajeActivo.oro;

        if (DOM.hudGold) DOM.hudGold.innerText = STATE.personajeActivo.oro;
        if (DOM.selectedGold) DOM.selectedGold.innerText = `Oro: ${STATE.personajeActivo.oro}`;
        if (DOM.badgeOro) DOM.badgeOro.innerText = `💰 ${STATE.personajeActivo.oro} oro`;

        mostrarToast(`Comprado: ${item.nombre}`, 'ok');
        cargarInventario(STATE.personajeActivo.id);
        pedirPersonajes();
    } catch (err) {
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

/* ==========================================================================
   INVENTARIO, COMBATE Y SUBIDA DE NIVEL
   ========================================================================== */
async function cargarInventario(personajeId) {
    if (!DOM.inventoryGrid) return;
    DOM.inventoryGrid.innerHTML = `<div class="empty-state"><span>⌛</span><p>Cargando mochila...</p></div>`;

    try {
        const res   = await fetch(`/api/inventario/?id=${personajeId}`);
        const items = await res.json();

        if (DOM.badgeItems) {
            DOM.badgeItems.innerText = `${items.length} objeto${items.length === 1 ? '' : 's'}`;
        }

        if (!items.length) {
            DOM.inventoryGrid.innerHTML = `<div class="empty-state"><span>🎒</span><p>Mochila vacía.</p></div>`;
            return;
        }

        DOM.inventoryGrid.innerHTML = items.map(it => {
            // Normalizamos la rareza para la clase CSS
            const rarClass = (it.rareza || 'Común').toLowerCase().replace('é', 'e');
            const isEquipped = Boolean(it.equipado);

            return `
                <div class="inv-item rar-${rarClass} ${isEquipped ? 'equipped' : ''}"
                     data-inv-id="${it.id}">
 
                    <div class="inv-icon">⚔️</div>
                    <strong>${it.item_nombre}</strong>
                    <span class="inv-rar">${it.rareza}</span>
                    <p>x${it.cantidad}</p>
 
                    ${isEquipped ? '<span class="equipped-tag">Equipado</span>' : ''}
 
                    <button
                        class="btn-toggle-equip"
                        data-inv-id="${it.id}"
                        data-equipado="${isEquipped}"
                        title="${isEquipped ? 'Desequipar' : 'Equipar'} ${it.item_nombre}"
                    >
                        ${isEquipped ? '🔴 Desequipar' : '🟢 Equipar'}
                    </button>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('❌ Error cargando inventario:', err);
        DOM.inventoryGrid.innerHTML = `<div class="empty-state"><span>⚠️</span><p>Error cargando inventario.</p></div>`;
    }
}


async function toggleEquipar(invId, estabaEquipado) {
    try {
        // Feedback visual inmediato: deshabilitamos el botón mientras viaja al servidor
        const btn = DOM.inventoryGrid.querySelector(`[data-inv-id="${invId}"].btn-toggle-equip`);
        if (btn) {
            btn.disabled = true;
            btn.innerText = '⏳ ...';
        }

        const res = await fetch(`/api/inventario/toggle/${invId}`, {
            method: 'POST'
            // Sin body — el endpoint solo necesita el ID de la URL
        });

        const resultado = await res.json();

        if (!resultado.ok) {
            mostrarToast(resultado.mensaje, 'warn');
            // Restauramos el botón si falló
            if (btn) {
                btn.disabled = false;
                btn.innerText = estabaEquipado ? '🔴 Desequipar' : '🟢 Equipar';
            }
            return;
        }

        // Actualizamos la tarjeta en el DOM sin hacer un fetch completo
        const card = DOM.inventoryGrid.querySelector(`.inv-item[data-inv-id="${invId}"]`);
        if (card) {
            const nuevoEstado = resultado.equipado; // True / False

            // Clase visual de la tarjeta
            card.classList.toggle('equipped', nuevoEstado);

            // Tag "Equipado"
            const tagExistente = card.querySelector('.equipped-tag');
            if (nuevoEstado && !tagExistente) {
                const tag = document.createElement('span');
                tag.className = 'equipped-tag';
                tag.innerText = 'Equipado';
                card.insertBefore(tag, card.querySelector('.btn-toggle-equip'));
            } else if (!nuevoEstado && tagExistente) {
                tagExistente.remove();
            }

            // Texto y estado del botón
            if (btn) {
                btn.disabled = false;
                btn.dataset.equipado = nuevoEstado;
                btn.title = `${nuevoEstado ? 'Desequipar' : 'Equipar'}`;
                btn.innerText = nuevoEstado ? '🔴 Desequipar' : '🟢 Equipar';
            }
        }

        escribirLog(resultado.mensaje);
        mostrarToast(resultado.mensaje, 'ok');

    } catch (err) {
        console.error('❌ Error en toggleEquipar:', err);
        mostrarToast('Error de red al cambiar estado.', 'error');
    }
}

if (DOM.inventoryGrid) {
    DOM.inventoryGrid.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-toggle-equip');
        if (!btn || btn.disabled) return;

        const invId       = Number(btn.dataset.invId);
        const equipado    = btn.dataset.equipado === 'true'; // string → boolean

        toggleEquipar(invId, equipado);
    });
}


async function cargarEnemigos() {
    if (!DOM.menuEnemigos) return;
    try {
        const res = await fetch('/api/enemigos');
        STATE.enemigos = await res.json();
        if (DOM.kpiEnemigos) DOM.kpiEnemigos.innerText = STATE.enemigos.length;
        DOM.menuEnemigos.innerHTML = '<option value="">Selecciona un enemigo...</option>' +
            STATE.enemigos.map(e => `<option value="${e.id}">${e.nombre} — Lv ${e.nivel} (${e.vida_max} HP)</option>`).join('');
    } catch {
        DOM.menuEnemigos.innerHTML = '<option value="">Error cargando enemigos</option>';
    }
}

if (DOM.btnIniciarCombate) {
    DOM.btnIniciarCombate.addEventListener('click', () => {
        if (!STATE.personajeActivo || !DOM.menuEnemigos.value) return mostrarToast("Héroe o enemigo inválido.", "warn");

        const enemigo = STATE.enemigos.find(e => String(e.id) === String(DOM.menuEnemigos.value));
        if(!enemigo) return;

        STATE.combate = {
            turno: 1,
            heroe: { id: STATE.personajeActivo.id, nombre: STATE.personajeActivo.nombre, hp: STATE.personajeActivo.vida_actual, hpMax: getVidaMax(STATE.personajeActivo), fuerza: STATE.personajeActivo.fuerza ?? 12 },
            enemigo: { id: enemigo.id, nombre: enemigo.nombre, hp: enemigo.vida_max, hpMax: enemigo.vida_max, dano: enemigo.dano_base },
            defendiendo: false
        };

        document.getElementById('hero-avatar').innerText = (STATE.personajeActivo.nombre || '?').charAt(0).toUpperCase();
        document.getElementById('hero-name').innerText = STATE.personajeActivo.nombre;
        document.getElementById('enemy-avatar').innerText = '👹';
        document.getElementById('enemy-name').innerText = enemigo.nombre;

        actualizarBarrasCombate();
        [DOM.combatArena, DOM.combatActions].forEach(el => el && el.classList.remove('hidden'));
        if (DOM.combatLog) DOM.combatLog.innerHTML = `<p>&gt; ¡${STATE.personajeActivo.nombre} desafía a ${enemigo.nombre}!</p>`;
        if (DOM.badgeTurno) DOM.badgeTurno.innerText = `Turno ${STATE.combate.turno}`;
    });
}

function actualizarBarrasCombate() {
    if (!STATE.combate) return;
    const { heroe: h, enemigo: e } = STATE.combate;
    document.getElementById('hero-hp-fill').style.width = `${Math.max(0, h.hp / h.hpMax * 100)}%`;
    document.getElementById('hero-hp-text').innerText = `${Math.max(0, h.hp)}/${h.hpMax}`;
    document.getElementById('enemy-hp-fill').style.width = `${Math.max(0, e.hp / e.hpMax * 100)}%`;
    document.getElementById('enemy-hp-text').innerText = `${Math.max(0, e.hp)}/${e.hpMax}`;
}

function logCombate(msg) {
    if (!DOM.combatLog) return;
    DOM.combatLog.insertAdjacentHTML('beforeend', `<p>&gt; ${msg}</p>`);
    DOM.combatLog.scrollTop = DOM.combatLog.scrollHeight;
}

function registrarAccionBackend(accion, danoInfligido, danoRecibido, resultado) {
    fetch('/api/combate/registro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_personaje: STATE.combate.heroe.id, id_enemigo: STATE.combate.enemigo.id, turno: STATE.combate.turno, accion, dano_infligido: danoInfligido, dano_recibido: danoRecibido, resultado })
    }).catch(() => {});
}

function turnoEnemigo() {
    if (!STATE.combate) return;
    if (STATE.combate.enemigo.hp <= 0) return finalizarCombate('victoria');

    const dano = STATE.combate.defendiendo ? Math.max(1, Math.floor(STATE.combate.enemigo.dano / 2)) : STATE.combate.enemigo.dano + rand(-2, 2);
    STATE.combate.heroe.hp -= dano;

    logCombate(`👹 ${STATE.combate.enemigo.nombre} te golpea por <b>${dano}</b> de daño${STATE.combate.defendiendo ? ' (mitigado)' : ''}.`);
    STATE.combate.defendiendo = false;
    actualizarBarrasCombate();

    if (STATE.combate.heroe.hp <= 0) return finalizarCombate('derrota');
    STATE.combate.turno++;
    if (DOM.badgeTurno) DOM.badgeTurno.innerText = `Turno ${STATE.combate.turno}`;
}

// OPTIMIZACIÓN: Delegación en Botones de Combate
if (DOM.combatActions) {
    DOM.combatActions.addEventListener('click', (e) => {
        const btn = e.target.closest('button');
        if (!btn || !STATE.combate) return;
        const accion = btn.dataset.accion;

        if (accion === 'huir') {
            logCombate(`🏃 Huyes del combate.`);
            registrarAccionBackend('huir', 0, 0, 'huida');
            return finalizarCombate('huida');
        }

        let danoInfligido = 0;
        if (accion === 'atacar') {
            danoInfligido = rand(8, 18);
            STATE.combate.enemigo.hp -= danoInfligido;
            logCombate(`🗡️ Atacas a ${STATE.combate.enemigo.nombre} y haces <b>${danoInfligido}</b> de daño.`);
        } else if (accion === 'especial') {
            danoInfligido = rand(18, 32);
            STATE.combate.enemigo.hp -= danoInfligido;
            logCombate(`✨ Habilidad especial: <b>${danoInfligido}</b> de daño.`);
        } else if (accion === 'defender') {
            STATE.combate.defendiendo = true;
            logCombate(`🛡️ Postura defensiva.`);
        }

        actualizarBarrasCombate();
        if (STATE.combate.enemigo.hp <= 0) {
            registrarAccionBackend(accion, danoInfligido, 0, 'victoria');
            return finalizarCombate('victoria');
        }

        registrarAccionBackend(accion, danoInfligido, 0, 'continua');
        setTimeout(turnoEnemigo, 600);
    });
}

function finalizarCombate(resultado) {
    if (DOM.combatActions) DOM.combatActions.classList.add('hidden');
    const msg = resultado === 'victoria' ? `🏆 <b>¡Victoria!</b> Has derrotado a ${STATE.combate.enemigo.nombre}.` :
                resultado === 'derrota' ? `💀 <b>Has caído</b> en combate...` : `Combate finalizado.`;
    logCombate(msg);
    STATE.combate = null;
}

async function subirNivelPersonaje() {
    if (!STATE.personajeActivo) return;
    try {
        const res = await fetch('/api/personaje/subir-nivel', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id_personaje: STATE.personajeActivo.id })
        });
        const resultado = await res.json();

        if (!resultado.ok) return mostrarToast(resultado.mensaje, 'warn');

        const datos = resultado.personaje;
        Object.assign(STATE.personajeActivo, {
            nivel: datos.nivel_actual, vida_max: datos.vida_max, vida_actual: datos.vida_actual,
            fuerza: datos.fuerza, agilidad: datos.agilidad, inteligencia: datos.inteligencia
        });

        if (DOM.hudLevel) DOM.hudLevel.innerText = datos.nivel_actual;
        if (DOM.hudHp) DOM.hudHp.innerText = `${datos.vida_actual}/${datos.vida_max}`;
        if (DOM.selectedLevel) DOM.selectedLevel.innerText = `Nivel: ${datos.nivel_actual}`;
        if (DOM.selectedHealth) DOM.selectedHealth.innerText = `Vida: ${datos.vida_actual}/${datos.vida_max}`;
        if (DOM.expInfo) DOM.expInfo.innerText = `EXP: ${datos.exp_restante} / ${datos.exp_para_siguiente_nivel}`;

        mostrarToast(resultado.mensaje, 'ok');
        pedirPersonajes();
    } catch (err) {
        console.error(err);
    }
}

if (DOM.btnSubirNivel) DOM.btnSubirNivel.addEventListener('click', subirNivelPersonaje);
if (DOM.btnRecargar) DOM.btnRecargar.addEventListener('click', pedirPersonajes);

/* ==========================================================================
   SOCKET.IO EVENTOS
   ========================================================================== */
if(socket) {
    socket.on('connect', () => {
        if (DOM.dot) DOM.dot.className = 'dot connected';
        if (DOM.text) DOM.text.innerText = 'Conectado';
        escribirLog("Conectado con éxito al servidor.");
        pedirPersonajes(); cargarTienda(); cargarEnemigos();
    });

    socket.on('disconnect', () => {
        if (DOM.dot) DOM.dot.className = 'dot disconnected';
        if (DOM.text) DOM.text.innerText = 'Desconectado';
        escribirLog("Se perdió la conexión.");
    });

    socket.on('status', (data) => escribirLog(data.msg));

    socket.on('personajes', (lista) => {
        STATE.personajes = lista || [];
        if (!DOM.contenedorPersonajes) return;
        if (DOM.kpiHeroes) DOM.kpiHeroes.innerText = STATE.personajes.length;

        if (!STATE.personajes.length) {
            if (DOM.menuPersonajes) DOM.menuPersonajes.innerHTML = '<option value="">No hay personajes</option>';
            if (DOM.personajeSeleccionado) DOM.personajeSeleccionado.classList.add('hidden');
            DOM.contenedorPersonajes.innerHTML = `<div class="empty-state"><span>🕯️</span><p>No hay aventureros.</p></div>`;
            if (DOM.contadorPersonajes) DOM.contadorPersonajes.innerText = "0 héroes";
            return;
        }

        llenarMenuPersonajes(STATE.personajes);
        if (DOM.contadorPersonajes) DOM.contadorPersonajes.innerText = `${STATE.personajes.length} héroe${STATE.personajes.length === 1 ? "" : "s"}`;

        DOM.contenedorPersonajes.innerHTML = STATE.personajes.map(p => {
            const claseNombre = NOMBRES_CLASES[p.id_clase] || 'Aventurero';
            return `
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
        }).join('');
    });
}