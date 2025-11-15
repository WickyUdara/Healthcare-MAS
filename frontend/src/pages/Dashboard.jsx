import React, { useState, useEffect } from "react";
import {
  getMetrics,
  getPatients,
  getWaitingList,
  getBeds,
} from "../api/apiClient";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import "./Dashboard.css";

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [patients, setPatients] = useState([]);
  const [waitingList, setWaitingList] = useState([]);
  const [beds, setBeds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [mRes, pRes, wRes, bRes] = await Promise.all([
        getMetrics(),
        getPatients(),
        getWaitingList(),
        getBeds(),
      ]);
      setMetrics(mRes.data);
      setPatients(pRes.data);
      setWaitingList(wRes.data);
      setBeds(bRes.data);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading)
    return (
      <div className="dashboard-page">
        <p>Loading...</p>
      </div>
    );

  if (!metrics)
    return (
      <div className="dashboard-page">
        <p>No data available</p>
      </div>
    );

  // Prepare ward occupancy data
  const wardData = Object.entries(metrics.by_ward || {}).map(
    ([name, data]) => ({
      name,
      occupied: data.occupied,
      available: data.available,
    })
  );

  // Prepare patient status data
  const patientStatusData = [
    { name: "Admitted", value: metrics.patients.admitted, color: "#4CAF50" },
    { name: "Waiting", value: metrics.patients.waiting, color: "#FF9800" },
    { name: "Critical", value: metrics.patients.critical, color: "#F44336" },
  ];

  // Prepare bed status data
  const bedStatusData = [
    { name: "Occupied", value: metrics.occupied, color: "#FF9800" },
    { name: "Available", value: metrics.available, color: "#4CAF50" },
    { name: "Cleaning", value: metrics.cleaning, color: "#2196F3" },
  ];

  return (
    <div className="dashboard-page">
      <h1>📈 Admin Dashboard</h1>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{metrics.total_beds}</div>
          <div className="metric-label">Total Beds</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{metrics.occupied}</div>
          <div className="metric-label">Occupied</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{metrics.available}</div>
          <div className="metric-label">Available</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{metrics.cleaning}</div>
          <div className="metric-label">Cleaning</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">
            {(metrics.occupancy_rate * 100).toFixed(0)}%
          </div>
          <div className="metric-label">Occupancy Rate</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{metrics.patients.total}</div>
          <div className="metric-label">Total Patients</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Bed Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={bedStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {bedStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Patient Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={patientStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {patientStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Occupancy by Ward</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={wardData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="occupied" stackId="a" fill="#FF9800" />
              <Bar dataKey="available" stackId="a" fill="#4CAF50" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="details-grid">
        <div className="details-card">
          <h3>Patient Statistics</h3>
          <table className="stats-table">
            <tbody>
              <tr>
                <td>Total Patients</td>
                <td>
                  <strong>{metrics.patients.total}</strong>
                </td>
              </tr>
              <tr>
                <td>Admitted</td>
                <td>
                  <strong>{metrics.patients.admitted}</strong>
                </td>
              </tr>
              <tr>
                <td>Waiting</td>
                <td>
                  <strong>{metrics.patients.waiting}</strong>
                </td>
              </tr>
              <tr>
                <td>Critical</td>
                <td>
                  <strong style={{ color: "#F44336" }}>
                    {metrics.patients.critical}
                  </strong>
                </td>
              </tr>
              <tr>
                <td>Avg Severity</td>
                <td>
                  <strong>
                    {metrics.patients.avg_severity.toFixed(1)}/100
                  </strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="details-card">
          <h3>Ward Breakdown</h3>
          <table className="stats-table">
            <tbody>
              {Object.entries(metrics.by_ward || {}).map(([ward, data]) => (
                <tr key={ward}>
                  <td>{ward}</td>
                  <td>
                    <strong>
                      {data.occupied}/{data.total}
                    </strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="details-card">
          <h3>System Health</h3>
          <div className="health-indicator">
            <span className="label">Occupancy Rate</span>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${metrics.occupancy_rate * 100}%`,
                  backgroundColor:
                    metrics.occupancy_rate > 0.8
                      ? "#F44336"
                      : metrics.occupancy_rate > 0.6
                      ? "#FF9800"
                      : "#4CAF50",
                }}
              ></div>
            </div>
            <span className="value">
              {(metrics.occupancy_rate * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
