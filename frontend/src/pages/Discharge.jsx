import React, { useState, useEffect } from "react";
import {
  getPatients,
  dischargePatient,
  getActivityLog,
} from "../api/apiClient";
import MessageBubble from "../components/MessageBubble";
import "./Discharge.css";

export default function Discharge() {
  const [patients, setPatients] = useState([]);
  const [activityLog, setActivityLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discharging, setDischarging] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [pRes, aRes] = await Promise.all([
        getPatients(),
        getActivityLog(20),
      ]);
      setPatients(pRes.data);
      setActivityLog(aRes.data);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDischarge = async (patientId) => {
    setDischarging(patientId);
    try {
      const response = await dischargePatient(patientId);
      setResult(response.data);
      setTimeout(() => fetchData(), 1000);
    } catch (err) {
      alert("Discharge failed: " + err.message);
      setDischarging(null);
    }
  };

  if (loading)
    return (
      <div className="discharge-page">
        <p>Loading...</p>
      </div>
    );

  const admittedPatients = patients.filter((p) => p.status === "admitted");

  return (
    <div className="discharge-page">
      <h1>🚪 Patient Discharge</h1>

      {result && (
        <div className="result-notification">
          <h2>✓ Discharge Initiated</h2>
          <p>{result.message}</p>
          <button onClick={() => setResult(null)}>Close</button>
        </div>
      )}

      <div className="discharge-content">
        <div className="section">
          <h2>Admitted Patients</h2>
          {admittedPatients.length === 0 ? (
            <p className="empty-message">No admitted patients</p>
          ) : (
            <div className="patients-list">
              {admittedPatients.map((patient) => (
                <div key={patient.id} className="patient-item">
                  <div className="patient-info">
                    <strong>{patient.name}</strong>
                    <span className="current-bed">
                      Bed: {patient.current_bed || "N/A"}
                    </span>
                    <span className="severity-badge">
                      {patient.severity_score.toFixed(0)}/100
                    </span>
                  </div>
                  <button
                    onClick={() => handleDischarge(patient.id)}
                    disabled={discharging === patient.id}
                    className="btn-discharge"
                  >
                    {discharging === patient.id
                      ? "⏳ Processing..."
                      : "Discharge"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="section">
          <h2>Recent Activity</h2>
          {activityLog.length === 0 ? (
            <p className="empty-message">No recent activity</p>
          ) : (
            <div className="activity-list">
              {activityLog.slice(0, 10).map((log) => (
                <MessageBubble key={log.id} message={log} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
