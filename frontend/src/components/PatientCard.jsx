import React from "react";
import "./PatientCard.css";

export default function PatientCard({ patient }) {
  const statusColors = {
    admitted: "#4CAF50",
    waiting: "#FF9800",
    discharged: "#999",
    critical: "#F44336",
  };

  const severityColor =
    patient.severity_score > 70
      ? "#F44336"
      : patient.severity_score > 40
      ? "#FF9800"
      : "#4CAF50";

  return (
    <div className="patient-card">
      <div className="patient-card-header">
        <h3>{patient.name}</h3>
        <span
          className="patient-status"
          style={{ backgroundColor: statusColors[patient.status] }}
        >
          {patient.status.toUpperCase()}
        </span>
      </div>
      <div className="patient-card-body">
        <p>
          <strong>Age:</strong> {patient.age} | <strong>Gender:</strong>{" "}
          {patient.gender}
        </p>
        <p>
          <strong>Severity:</strong>
          <span
            className="severity-badge"
            style={{ backgroundColor: severityColor }}
          >
            {patient.severity_score.toFixed(0)}/100
          </span>
        </p>
        {patient.current_bed && (
          <p>
            <strong>Bed:</strong> {patient.current_bed}
          </p>
        )}
        {patient.is_emergency && (
          <p className="emergency-badge">⚠️ EMERGENCY</p>
        )}
      </div>
    </div>
  );
}
