import React, { useState, useEffect } from "react";
import {
  getBeds,
  getPatients,
  getWaitingList,
  getActivityLog,
} from "../api/apiClient";
import BedCard from "../components/BedCard";
import PatientCard from "../components/PatientCard";
import MessageBubble from "../components/MessageBubble";
import "./BedAssignment.css";

export default function BedAssignment() {
  const [beds, setBeds] = useState([]);
  const [patients, setPatients] = useState([]);
  const [waitingList, setWaitingList] = useState([]);
  const [activityLog, setActivityLog] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [bRes, pRes, wRes, aRes] = await Promise.all([
        getBeds(),
        getPatients(),
        getWaitingList(),
        getActivityLog(15),
      ]);

      // Log responses for debugging
      console.log("Beds response:", bRes);
      console.log("Patients response:", pRes);
      console.log("Waiting list response:", wRes);
      console.log("Activity log response:", aRes);

      setBeds(bRes.data || bRes || []);
      setPatients(pRes.data || pRes || []);
      setWaitingList(wRes.data || wRes || []);
      setActivityLog(aRes.data || aRes || []);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching data:", err);
      setBeds([]);
      setPatients([]);
      setWaitingList([]);
      setActivityLog([]);
      setLoading(false);
    }
  };

  if (loading)
    return (
      <div className="bed-assignment-page">
        <p>Loading...</p>
      </div>
    );

  const wards = ["ICU", "GENERAL", "SURGERY", "MATERNITY"];
  const groupedBeds = {};
  wards.forEach((ward) => {
    groupedBeds[ward] = beds.filter((b) => b.ward_name === ward);
  });

  const admittedPatients = patients.filter((p) => p.status === "admitted");
  const occupancyRate =
    beds.length > 0
      ? (beds.filter((b) => b.status === "occupied").length / beds.length) * 100
      : 0;

  return (
    <div className="bed-assignment-page">
      <h1>🛏️ Bed Assignment & Auto-Allocation</h1>

      <div className="stats-bar">
        <div className="stat">
          <span className="stat-label">Total Beds</span>
          <span className="stat-value">{beds.length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Occupied</span>
          <span className="stat-value" style={{ color: "#FF9800" }}>
            {beds.filter((b) => b.status === "occupied").length}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Available</span>
          <span className="stat-value" style={{ color: "#4CAF50" }}>
            {beds.filter((b) => b.status === "available").length}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Cleaning</span>
          <span className="stat-value" style={{ color: "#2196F3" }}>
            {beds.filter((b) => b.status === "cleaning").length}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Occupancy</span>
          <span className="stat-value">{occupancyRate.toFixed(0)}%</span>
        </div>
        <div className="stat">
          <span className="stat-label">Waiting</span>
          <span className="stat-value" style={{ color: "#FF9800" }}>
            {waitingList.length}
          </span>
        </div>
      </div>

      <div className="assignment-content">
        <div className="beds-section">
          <h2>Hospital Beds by Ward</h2>
          {wards.map((ward) => (
            <div key={ward} className="ward-section">
              <h3>{ward} Ward</h3>
              <div className="beds-grid">
                {groupedBeds[ward].map((bed) => (
                  <BedCard key={bed.id} bed={bed} />
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="sidebar">
          <div className="section">
            <h3>Currently Admitted</h3>
            {admittedPatients.length === 0 ? (
              <p className="empty-message">No admitted patients</p>
            ) : (
              <div className="patients-list">
                {admittedPatients.map((p) => (
                  <PatientCard key={p.id} patient={p} />
                ))}
              </div>
            )}
          </div>

          <div className="section">
            <h3>Waiting List ({waitingList.length})</h3>
            {waitingList.length === 0 ? (
              <p className="empty-message">No waiting patients</p>
            ) : (
              <div className="waiting-list">
                {waitingList.map((entry, idx) => (
                  <div key={entry.id} className="waiting-item">
                    <span className="position">#{entry.position}</span>
                    <div className="waiting-info">
                      <strong>{entry.patient_name}</strong>
                      <small>
                        {(entry.wait_time_seconds / 60).toFixed(1)}m wait
                      </small>
                    </div>
                    <span className="severity-badge">
                      {entry.severity.toFixed(0)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="section">
            <h3>Recent Activity</h3>
            <div className="activity-list">
              {activityLog.slice(0, 5).map((log) => (
                <MessageBubble key={log.id} message={log} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
