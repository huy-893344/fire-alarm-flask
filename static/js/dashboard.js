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

  // 2) Khởi tạo Firebase
  firebase.initializeApp(firebaseConfig);

  // 3) Tham chiếu tới node DataSensorRealTime
  const dbRef = firebase.database().ref('DataSensorRealTime');
  const tbody = document.getElementById('sensor-data');

  // 4) Nghe realtime
  dbRef.on('value',
    snapshot => {
      const data = snapshot.val() || {};
      tbody.innerHTML = '';

      // Nếu chưa có node nào
      if (Object.keys(data).length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="text-center py-4">Chưa có dữ liệu</td>
          </tr>
        `;
        return;
      }

      // Duyệt từng thiết bị
      Object.entries(data).forEach(([sid, item]) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${item.send_address || sid}</td>
          <td>${item.temperature != null ? item.temperature : '—'}</td>
          <td>${item.humidity    != null ? item.humidity    : '—'}</td>
          <td>${item.mq2         != null ? item.mq2         : '—'}</td>
          <td>${item.fire ? '<span class="text-danger fw-bold">Có</span>' : 'Không'}</td>
        `;
        tbody.appendChild(tr);
      });
    },
    error => {
      console.error('Firebase read failed:', error);
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center text-danger py-4">
            Lỗi kết nối dữ liệu
          </td>
        </tr>
      `;
    }
  );
});
