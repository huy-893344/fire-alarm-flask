function fetchRealtimeData() {
  fetch('/api/realtime')
    .then(response => response.json())
    .then(data => {
      const tableBody = document.getElementById("sensor-data");
      tableBody.innerHTML = '';

      Object.keys(data).forEach(sensor => {
        const d = data[sensor];
        const fireText = d.fire ? 'Có' : 'Không';
        const fireClass = d.fire ? 'table-danger fw-bold' : '';

        const row = `
          <tr class="${fireClass}">
            <td>${d.address || sensor}</td>
            <td>${d.temperature ?? 'N/A'}</td>
            <td>${d.humidity ?? 'N/A'}</td>
            <td>${d.mq2 ?? 'N/A'}</td>
            <td>${fireText}</td>
          </tr>
        `;
        tableBody.innerHTML += row;
      });
    })
    .catch(error => {
      console.error("Lỗi khi tải dữ liệu:", error);
    });
}

setInterval(fetchRealtimeData, 3000);
window.onload = fetchRealtimeData;
