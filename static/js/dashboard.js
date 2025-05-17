// static/js/dashboard.js
// This file initializes Firebase and listens for real-time updates

document.addEventListener('DOMContentLoaded', () => {
  // Firebase Web SDK v9 compatibility
  // Be sure to include <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-app-compat.js"></script>
  // and <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-database-compat.js"></script>

  // 1) Firebase configuration – replace placeholders with your project's values
  const firebaseConfig = {
    apiKey: "AIzaSyA3mHhx4atZVfMe-cxgU3hbqHl3ieHuD4U",
    authDomain: "tutrungtambaochay.firebaseapp.com",
    databaseURL: "https://tutrungtambaochay-default-rtdb.firebaseio.com",
    projectId: "tutrungtambaochay",
    storageBucket: "tutrungtambaochay.firebasestorage.app",
    messagingSenderId: "553147068654",
    appId: "1:553147068654:web:8274efbef19bacf47883ff",
 
  };

  // 2) Initialize Firebase
  firebase.initializeApp(firebaseConfig);

  // 3) Reference the DataSensorRealTime node
  const dbRef = firebase.database().ref('DataSensorRealTime');
  const tbody = document.getElementById('sensor-data');

  // 4) Listen for real-time value changes
  dbRef.on('value', snapshot => {
    const data = snapshot.val() || {};
    tbody.innerHTML = '';

    // If no data, show placeholder row
    if (Object.keys(data).length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center py-6">Chưa có dữ liệu</td></tr>';
      return;
    }

    // Populate table rows
    Object.entries(data).forEach(([sid, item]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="px-4 py-2">${item.send_address || sid}</td>
        <td class="px-4 py-2">${item.temperature ?? '—'}</td>
        <td class="px-4 py-2">${item.humidity ?? '—'}</td>
        <td class="px-4 py-2">${item.mq2 ?? '—'}</td>
        <td class="px-4 py-2">${item.fire ? '<span class="text-red-600 font-semibold">Có</span>' : 'Không'}</td>
      `;
      tbody.appendChild(tr);
    });
  });
});
