document.addEventListener('DOMContentLoaded', () => {
  const firebaseConfig = {
    apiKey: "AIzaSyC13VZFz4aOjfPhpU7rqjZ-F8Ja-4MJkcc",
    authDomain: "pham-quoc-anh.firebaseapp.com",
    databaseURL: "https://pham-quoc-anh-default-rtdb.firebaseio.com",
    projectId: "pham-quoc-anh",
    storageBucket: "pham-quoc-anh.firebasestorage.app",
    messagingSenderId: "170698691755",
    appId: "1:170698691755:web:30a490b90e2c803410d3ee"
  };

  firebase.initializeApp(firebaseConfig);

  const db = firebase.database();
  const tbody = document.getElementById('sensor-data');

  const nodeRefs = {
    humi: db.ref('esp32_humi'),
    temp: db.ref('esp32_temp'),
    mq2: db.ref('esp32_mq2'),
    fire: db.ref('esp32_lm393')
  };

  const sensorData = {}; // chứa dữ liệu theo sid

  function updateTable() {
    tbody.innerHTML = '';

    const sids = Object.keys(sensorData);
    if (sids.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center py-4 text-muted">Chưa có dữ liệu</td>
        </tr>
      `;
      return;
    }

    sids.forEach(sid => {
      const d = sensorData[sid];
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${sid}</td>
        <td>${d.temp ?? '-'}</td>
        <td>${d.humi ?? '-'}</td>
        <td>${d.mq2 ?? '-'}</td>
        <td>${d.fire != null ? (d.fire == 1 ? 'Có' : 'Không') : '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Lắng nghe từng node
  Object.entries(nodeRefs).forEach(([key, ref]) => {
    ref.on('value', snapshot => {
      const data = snapshot.val() || {};

      Object.entries(data).forEach(([sid, val]) => {
        if (!sensorData[sid]) {
          sensorData[sid] = { temp: null, humi: null, mq2: null, fire: null };
        }
        sensorData[sid][key] = val;
      });

      updateTable();
    });
  });
});
