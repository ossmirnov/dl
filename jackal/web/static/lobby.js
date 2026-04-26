const createForm = document.getElementById('create-form');
const joinForm = document.getElementById('join-form');
const seedInput = document.getElementById('seed');
const roomIdInput = document.getElementById('room-id');

createForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const body = {};
  if (seedInput.value !== '') body.seed = Number(seedInput.value);
  const r = await fetch('/api/rooms', {
    method: 'POST',
    headers: {'content-type': 'application/json'},
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    alert('failed to create room');
    return;
  }
  const data = await r.json();
  window.location.href = `/room/${data.room_id}`;
});

joinForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const id = roomIdInput.value.trim();
  if (id) window.location.href = `/room/${id}`;
});
