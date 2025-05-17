// static/js/dashboard.js
// This file initializes Firebase and listens for real-time updates
// Ensure you have included in your base.html before this script:
// <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-app-compat.js"></script>
// <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-database-compat.js"></script>

document.addEventListener('DOMContentLoaded', () => {
  // 1) Firebase configuration – using your project credentials
  const firebaseConfig = {
    apiKey: "AIzaSyC13VZFz4aOjfPhpU7rqjZ-F8Ja-4MJkcc",
    authDomain: "pham-quoc-anh.firebaseapp.com",
    databaseURL: "https://pham-quoc-anh-default-rtdb.firebaseio.com",
    projectId: "pham-quoc-anh",
    storageBucket: "pham-quoc-anh.firebasestorage.app",
    messagingSenderId: "170698691755",
    appId: "1:170698691755:web:30a490b90e2c803410d3ee"
  };

  // 2) Initialize Firebase
  firebase.initializeApp(firebaseConfig);

  // 3) Reference the DataSensorRealTime node in your database
  const dbRef = firebase.database().ref('DataSensorRealTime');
  const tbody = document.getElementById('sensor-data');

  // 4) Listen for real-time updates
  dbRef.on('value', snapshot => {
    const data = snapshot.val();
    tbody.innerHTML = '';

    // Handle no-data case
    if (!data || Object.keys(data).length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center py-6">Chưa có dữ liệu</td></tr>';
      return;
    }

    // Populate table rows (each child is a sensor node)
    Object.entries(data).forEach(([sid, item]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="px-4 py-2">${item.send_address || sid}</td>
        <td class="px-4 py-2">${item.temperature != null ? item.temperature : '—'}</td>
        <td class="px-4 py-2">${item.humidity    != null ? item.humidity    : '—'}</td>
        <td class="px-4 py-2">${item.mq2         != null ? item.mq2         : '—'}</td>
        <td class="px-4 py-2">${item.fire ? '<span class="text-red-600 font-semibold">Có</span>' : 'Không'}</td>
      `;
      tbody.appendChild(tr);
    });
  }, error => {
    console.error('Firebase read failed:', error);
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-red-600 py-6">Lỗi kết nối dữ liệu</td></tr>';
  });
});
