const CELL = 60;
const SIZE = 10;

const TYPES = [
  'empty', 'money', 'swap', 'tunnel', 'double', 'fly',
  'swamp', 'teleport', 'stone', 'thief', 'wizard', 'normalize',
  'home_red', 'home_blue',
];

const CLOSED_FILE = 'back';

const TYPE_LABEL = {
  closed: '?',
  empty: '',
  money: '$',
  swap: '↔',
  tunnel: '⇩',
  double: '×2',
  fly: '✈',
  swamp: '≈',
  teleport: '◎',
  stone: '■',
  thief: '✋',
  wizard: '✦',
  normalize: '○',
  home_red: 'R',
  home_blue: 'B',
};

const TYPE_COLOR = {
  closed: '#3b4a64',
  empty: '#d4c094',
  money: '#fcd34d',
  swap: '#a78bfa',
  tunnel: '#475569',
  double: '#fb923c',
  fly: '#7dd3fc',
  swamp: '#65a30d',
  teleport: '#22d3ee',
  stone: '#6b7280',
  thief: '#dc2626',
  wizard: '#e879f9',
  normalize: '#f5f5f5',
  home_red: '#ef4444',
  home_blue: '#3b82f6',
};

const KEY_DIR = {
  ArrowUp: 'up', w: 'up', W: 'up',
  ArrowDown: 'down', s: 'down', S: 'down',
  ArrowLeft: 'left', a: 'left', A: 'left',
  ArrowRight: 'right', d: 'right', D: 'right',
};

const DELTA = {up: [-1, 0], down: [1, 0], left: [0, -1], right: [0, 1]};

const roomId = window.location.pathname.split('/').pop();
document.getElementById('room-id-tag').textContent = roomId;

const canvas = document.getElementById('board');
const ctx = canvas.getContext('2d');
canvas.focus();

const elYou = document.getElementById('you-tag');
const elConn = document.getElementById('conn-tag');
const elBalRed = document.getElementById('bal-red');
const elBalBlue = document.getElementById('bal-blue');
const elAbRed = document.getElementById('ab-red');
const elAbBlue = document.getElementById('ab-blue');
const elTurnArrow = document.getElementById('turn-arrow');
const elBanner = document.getElementById('banner');
const elRematch = document.getElementById('rematch');
const elLog = document.getElementById('log');

const images = {};
const imageMissing = {};
function loadImages() {
  for (const t of TYPES) {
    const img = new Image();
    img.src = `/media/tile_${t}.png`;
    img.onload = () => { images[t] = img; draw(); };
    img.onerror = () => { imageMissing[t] = true; };
  }
  const back = new Image();
  back.src = `/media/tile_${CLOSED_FILE}.png`;
  back.onload = () => { images['closed'] = back; draw(); };
  back.onerror = () => { imageMissing['closed'] = true; };
  for (const c of ['red', 'blue']) {
    const img = new Image();
    img.src = `/media/player_${c}.png`;
    img.onload = () => { images[`player_${c}`] = img; draw(); };
    img.onerror = () => { imageMissing[`player_${c}`] = true; };
  }
}
loadImages();

let state = null;
let me = null;
let displayPos = {red: null, blue: null};
let animating = false;

const sessionKey = `jackal_session_${roomId}`;
let sessionId = localStorage.getItem(sessionKey);
if (!sessionId) {
  sessionId = (crypto.randomUUID && crypto.randomUUID()) ||
    (Date.now().toString(36) + Math.random().toString(36).slice(2));
  localStorage.setItem(sessionKey, sessionId);
}

const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
let ws = null;
let reconnectDelay = 500;

function connect() {
  ws = new WebSocket(`${proto}//${location.host}/ws/${roomId}?session=${encodeURIComponent(sessionId)}`);
  ws.addEventListener('open', () => {
    elConn.classList.add('ok');
    elConn.title = 'connected';
    reconnectDelay = 500;
  });
  ws.addEventListener('close', (e) => {
    elConn.classList.remove('ok');
    elConn.title = 'disconnected';
    if (e.code === 4000) {
      appendLog('replaced by another tab', 'error');
      return;
    }
    if (e.code === 4001) {
      appendLog('missing session id; reload the page', 'error');
      return;
    }
    appendLog(`disconnected, reconnecting in ${reconnectDelay}ms`, 'error');
    setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 10000);
  });
  ws.addEventListener('error', () => appendLog('connection error', 'error'));
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.type === 'assigned') {
      me = m.color;
      elYou.textContent = me === 'spectator' ? 'spectating' : `you are ${me}`;
    } else if (m.type === 'state') {
      onState(m.state);
    } else if (m.type === 'events') {
      for (const e of m.events) appendEvent(e);
    } else if (m.type === 'error') {
      appendLog(`error: ${m.message}`, 'error');
    }
  });
}
connect();

function send(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

function onState(s) {
  const prev = state;
  state = s;
  elBalRed.textContent = s.players.red.balance;
  elBalBlue.textContent = s.players.blue.balance;
  elAbRed.textContent = s.players.red.abilities.join(' ');
  elAbBlue.textContent = s.players.blue.abilities.join(' ');
  elTurnArrow.classList.toggle('flip', s.turn === 'blue');
  if (s.winner) {
    elBanner.textContent = `${s.winner} wins!`;
    elBanner.classList.remove('hidden');
    if (me !== 'spectator') {
      elRematch.classList.remove('hidden');
    }
  } else {
    elBanner.classList.add('hidden');
    elRematch.classList.add('hidden');
  }
  for (const c of ['red', 'blue']) {
    const target = s.players[c].pos;
    if (!displayPos[c]) {
      displayPos[c] = [target[0], target[1]];
    } else if (displayPos[c][0] !== target[0] || displayPos[c][1] !== target[1]) {
      animateTo(c, target, prev);
    }
  }
  draw();
}

function animateTo(color, target, prev) {
  const start = displayPos[color].slice();
  const t0 = performance.now();
  const dur = 200;
  animating = true;
  function step(t) {
    const k = Math.min(1, (t - t0) / dur);
    displayPos[color] = [
      start[0] + (target[0] - start[0]) * k,
      start[1] + (target[1] - start[1]) * k,
    ];
    draw();
    if (k < 1) requestAnimationFrame(step);
    else { displayPos[color] = target.slice(); animating = false; draw(); }
  }
  requestAnimationFrame(step);
}

function appendEvent(e) {
  let txt = '';
  if (e.kind === 'opened') txt = `cell ${e.pos.join(',')} opened: ${e.cell_type}`;
  else if (e.kind === 'effect') txt = `${e.actor} triggered ${e.cell_type} at ${e.pos.join(',')}`;
  else if (e.kind === 'moved') txt = `${e.actor} moved to ${e.pos.join(',')}`;
  else if (e.kind === 'flew') txt = `${e.actor} flew to ${e.pos.join(',')}`;
  else if (e.kind === 'bounced') txt = `${e.actor} bounced off ${e.pos.join(',')}`;
  else if (e.kind === 'skipped') txt = `${e.actor} skipped`;
  else if (e.kind === 'abilities_cleared') txt = `${e.actor} abilities cleared (${e.reason})`;
  else if (e.kind === 'win') return appendLog(`${e.actor} wins!`, 'win');
  else txt = JSON.stringify(e);
  appendLog(txt);
}

function appendLog(text, cls) {
  const el = document.createElement('div');
  el.className = 'entry' + (cls ? ' ' + cls : '');
  el.textContent = text;
  elLog.appendChild(el);
  elLog.scrollTop = elLog.scrollHeight;
}

function draw() {
  if (!state) {
    ctx.fillStyle = '#1d2a3e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    return;
  }
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      drawCell(r, c, state.cells[r][c]);
    }
  }
  drawPlayer('red');
  drawPlayer('blue');
  if (myFlying()) {
    ctx.strokeStyle = '#7dd3fc';
    ctx.lineWidth = 3;
    ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);
  }
}

function drawCell(r, c, cell) {
  const x = c * CELL;
  const y = r * CELL;
  const t = cell.type;
  if (images[t] && !imageMissing[t]) {
    ctx.drawImage(images[t], x, y, CELL, CELL);
  } else {
    ctx.fillStyle = TYPE_COLOR[t] || '#222';
    ctx.fillRect(x + 1, y + 1, CELL - 2, CELL - 2);
    ctx.strokeStyle = '#0f1722';
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, y + 0.5, CELL - 1, CELL - 1);
    let label = TYPE_LABEL[t] || '';
    if (t === 'money' && cell.value) label = '$' + cell.value;
    if (label) {
      ctx.fillStyle = darkText(t) ? '#0f1722' : '#fff';
      ctx.font = 'bold 16px system-ui';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, x + CELL / 2, y + CELL / 2);
    }
  }
}

function darkText(t) {
  return ['empty', 'money', 'fly', 'normalize', 'teleport', 'wizard'].includes(t);
}

function drawPlayer(color) {
  if (!state) return;
  const dp = displayPos[color];
  if (!dp) return;
  const [r, c] = dp;
  const x = c * CELL + CELL / 2;
  const y = r * CELL + CELL / 2;
  const key = `player_${color}`;
  if (images[key] && !imageMissing[key]) {
    ctx.drawImage(images[key], x - CELL / 3, y - CELL / 3, (CELL * 2) / 3, (CELL * 2) / 3);
  } else {
    ctx.beginPath();
    ctx.arc(x, y, CELL / 3, 0, Math.PI * 2);
    ctx.fillStyle = color === 'red' ? '#ef4444' : '#3b82f6';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#0f1722';
    ctx.stroke();
  }
}

function myFlying() {
  if (!state || !me || me === 'spectator') return false;
  return state.players[me].abilities.includes('fly');
}

function isMyTurn() {
  return state && me === state.turn && !state.winner;
}

window.addEventListener('keydown', (e) => {
  const dir = KEY_DIR[e.key];
  if (!dir || !isMyTurn()) return;
  e.preventDefault();
  send({type: 'move', dir});
});

canvas.addEventListener('click', (e) => {
  if (!state || !isMyTurn()) return;
  const rect = canvas.getBoundingClientRect();
  const sx = canvas.width / rect.width;
  const sy = canvas.height / rect.height;
  const c = Math.floor((e.clientX - rect.left) * sx / CELL);
  const r = Math.floor((e.clientY - rect.top) * sy / CELL);
  if (r < 0 || r >= SIZE || c < 0 || c >= SIZE) return;
  if (myFlying()) {
    send({type: 'fly', r, c});
    return;
  }
  const meState = state.players[me];
  const dr = r - meState.pos[0];
  const dc = c - meState.pos[1];
  for (const [dir, [ddr, ddc]] of Object.entries(DELTA)) {
    const step = state.players[me].abilities.includes('double') ? 2 : 1;
    if (dr === ddr * step && dc === ddc * step) {
      send({type: 'move', dir});
      return;
    }
  }
});

document.querySelectorAll('#dpad button').forEach((btn) => {
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    if (!isMyTurn()) return;
    const dir = btn.dataset.dir;
    if (dir) send({type: 'move', dir});
  });
});

elRematch.addEventListener('click', () => {
  send({type: 'rematch'});
});

draw();
