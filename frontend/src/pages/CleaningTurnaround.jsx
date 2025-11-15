import React, { useState, useEffect } from "react";
import { getBeds } from "../api/apiClient";
import "./CleaningTurnaround.css";

export default function CleaningTurnaround() {
  const [beds, setBeds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const res = await getBeds();
      setBeds(res.data);
    } catch (err) {
      console.error("Error fetching beds:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading)
    return (
      <div className="cleaning-page">
        <p>Loading...</p>
      </div>
    );

  const cleaningBeds = beds.filter((b) => b.status === "cleaning");
  const allBeds = beds;

  return (
    <div className="cleaning-page">
      <h1>🧹 Bed Cleaning & Turnaround</h1>

      <div className="cleaning-info">
        <p>
          Standard cleaning time: <strong>10 seconds</strong> (simulated)
        </p>
        <p>
          Cleaning beds: <strong>{cleaningBeds.length}</strong> | Total beds:{" "}
          <strong>{allBeds.length}</strong>
        </p>
      </div>

      <div className="beds-grid">
        {allBeds.map((bed) => (
          <div key={bed.id} className={`bed-status-card ${bed.status}`}>
            <div className="bed-number">{bed.bed_number}</div>
            <div className="bed-ward">{bed.ward_name}</div>

            {bed.status === "cleaning" && (
              <div className="cleaning-animation">
                <div className="spinner"></div>
                <div className="cleaning-time">Cleaning...</div>
              </div>
            )}

            <div className={`status-indicator ${bed.status}`}>
              {bed.status === "available" && "✓ Available"}
              {bed.status === "occupied" && "👤 Occupied"}
              {bed.status === "cleaning" && "🧹 Cleaning"}
              {bed.status === "maintenance" && "⚠️ Maintenance"}
            </div>

            {bed.current_patient_name && (
              <div className="current-patient">{bed.current_patient_name}</div>
            )}
          </div>
        ))}
      </div>

      {cleaningBeds.length === 0 && (
        <div className="empty-state">
          <p>No beds currently cleaning</p>
        </div>
      )}
    </div>
  );
}
