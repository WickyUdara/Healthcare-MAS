import React, { useState } from "react";
import { admitPatient } from "../api/apiClient";
import "./Admission.css";

export default function Admission() {
  const [formData, setFormData] = useState({
    name: "John Smith",
    age: 65,
    gender: "Male",
    symptoms: "Chest pain, shortness of breath",
    heart_rate: 98,
    blood_pressure: "160/100",
    oxygen_saturation: 92,
    is_emergency: false,
    preferred_ward: "ICU",
  });

  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? checked
          : type === "number"
          ? Number(value)
          : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSubmitted(true);

    try {
      const response = await admitPatient(formData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Admission failed");
    } finally {
      setLoading(false);
    }
  };

  if (submitted && result) {
    return (
      <div className="admission-page">
        <div className="form-container">
          <h1>✓ Patient Admitted</h1>
          <div className="result-box">
            <div className="result-header">
              <h2>{result.patient_name}</h2>
              <span className={`status-badge ${result.status}`}>
                {result.status === "admitted"
                  ? "🛏️ ADMITTED"
                  : "⏳ ON WAITING LIST"}
              </span>
            </div>

            <div className="result-details">
              <div className="detail-row">
                <strong>Patient ID:</strong>
                <span>{result.patient_id}</span>
              </div>
              <div className="detail-row">
                <strong>Severity Score:</strong>
                <span
                  style={{
                    color:
                      result.severity_score > 70
                        ? "#F44336"
                        : result.severity_score > 40
                        ? "#FF9800"
                        : "#4CAF50",
                    fontWeight: "bold",
                  }}
                >
                  {result.severity_score.toFixed(0)}/100
                </span>
              </div>
              <div className="detail-row">
                <strong>Assessment:</strong>
                <span>{result.severity_explanation}</span>
              </div>
              {result.assigned_bed && (
                <div className="detail-row">
                  <strong>Assigned Bed:</strong>
                  <span>{result.assigned_bed}</span>
                </div>
              )}
              {result.waiting_list_position && (
                <div className="detail-row">
                  <strong>Waiting List Position:</strong>
                  <span>#{result.waiting_list_position}</span>
                </div>
              )}
              <div className="detail-row">
                <strong>Transaction ID:</strong>
                <span className="transaction-id">{result.transaction_id}</span>
              </div>
            </div>

            <div className="result-message">
              <p>
                {result.status === "admitted"
                  ? "✓ Patient has been successfully assigned to a bed and admitted to the hospital."
                  : "⏳ Patient has been placed on the waiting list. They will be assigned to an available bed automatically when one becomes free."}
              </p>
            </div>

            <button
              onClick={() => {
                setSubmitted(false);
                setResult(null);
              }}
              className="btn-primary"
            >
              Admit Another Patient
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admission-page">
      <div className="form-container">
        <h1>📋 Patient Admission</h1>
        <form onSubmit={handleSubmit} className="admission-form">
          <div className="form-group">
            <label>Patient Name *</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Age *</label>
              <input
                type="number"
                name="age"
                value={formData.age}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Gender *</label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                required
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Symptoms *</label>
            <textarea
              name="symptoms"
              value={formData.symptoms}
              onChange={handleChange}
              required
            ></textarea>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Heart Rate (bpm) *</label>
              <input
                type="number"
                name="heart_rate"
                value={formData.heart_rate}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Blood Pressure *</label>
              <input
                type="text"
                name="blood_pressure"
                value={formData.blood_pressure}
                onChange={handleChange}
                placeholder="e.g., 120/80"
                required
              />
            </div>
            <div className="form-group">
              <label>Oxygen Saturation (%) *</label>
              <input
                type="number"
                name="oxygen_saturation"
                value={formData.oxygen_saturation}
                onChange={handleChange}
                step="0.1"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Preferred Ward</label>
              <select
                name="preferred_ward"
                value={formData.preferred_ward}
                onChange={handleChange}
              >
                <option value="">Any</option>
                <option value="ICU">ICU</option>
                <option value="GENERAL">General</option>
                <option value="SURGERY">Surgery</option>
                <option value="MATERNITY">Maternity</option>
              </select>
            </div>
            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  name="is_emergency"
                  checked={formData.is_emergency}
                  onChange={handleChange}
                />
                Emergency Case
              </label>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "⏳ Admitting..." : "✓ Admit Patient"}
          </button>
        </form>
      </div>
    </div>
  );
}
