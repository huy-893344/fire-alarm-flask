// dashboard.js

const tableBody = document.getElementById("sensor-data");
const socket = io();

[1, 2, 3].forEach(n => {
  socket.on(`update_data_sensor${n}`, data => {
    const rowId = `row${n}`;
    let row = document.getElementById(rowId);

    const fireStatus = data.fire === 1 ? '🔥 Có cháy' : '✔️ An toàn';
    const html = `
      <td>${data.address}</td>
      <td>${data.temperature.toFixed(1)} °C</td>
      <td>${data.humidity.toFixed(1)} %</td>
      <td>${data.mq2.toFixed(0)} ppm</td>
      <td>${fireStatus}</td>
    `;

    if (!row) {
      row = document.createElement("tr");
      row.id = rowId;
      row.innerHTML = html;
      tableBody.appendChild(row);
    } else {
      row.innerHTML = html;
    }
  });
});

function logout() {
  window.location.href = "/logout";
}
