import React from "react";
import "./BedCard.css";

export default function BedCard({ bed }) {
  const statusColors = {
    available: "#4CAF50",
    occupied: "#FF9800",
    cleaning: "#2196F3",
    maintenance: "#9C27B0",
  };

  return (
    <div
      className="bed-card"
      style={{ borderLeftColor: statusColors[bed.status] || "#ccc" }}
    >
      <div className="bed-card-header">
        <h3>{bed.bed_number}</h3>
        <span className="bed-status">{bed.status.toUpperCase()}</span>
      </div>
      {bed.current_patient_name && (
        <div className="bed-card-body">
          <p>
            <strong>Patient:</strong> {bed.current_patient_name}
          </p>
        </div>
      )}
    </div>
  );
}
