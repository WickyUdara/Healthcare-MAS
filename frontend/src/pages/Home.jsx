import React from "react";
import { Link } from "react-router-dom";
import "./Home.css";

export default function Home() {
  return (
    <div className="home-page">
      <div className="hero">
        <h1>🏥 Hospital Bed Management System</h1>
        <p>Multi-Agent System for Intelligent Hospital Resource Allocation</p>
      </div>

      <div className="features-grid">
        <Link to="/admission" className="feature-card">
          <div className="feature-icon">📋</div>
          <h3>Patient Admission</h3>
          <p>
            Admit new patients and automatically assign beds based on severity
            and availability
          </p>
        </Link>

        <Link to="/bed-assignment" className="feature-card">
          <div className="feature-icon">🛏️</div>
          <h3>Bed Assignment</h3>
          <p>
            View bed allocation and monitor auto-assignment from waiting list
          </p>
        </Link>

        <Link to="/cleaning" className="feature-card">
          <div className="feature-icon">🧹</div>
          <h3>Cleaning & Turnaround</h3>
          <p>Monitor bed cleaning process and turnaround times</p>
        </Link>

        <Link to="/discharge" className="feature-card">
          <div className="feature-icon">🚪</div>
          <h3>Patient Discharge</h3>
          <p>Discharge patients and initiate automatic bed cleaning</p>
        </Link>

        <Link to="/activity-log" className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Agent Activity Log</h3>
          <p>View real-time agent communications and message exchanges</p>
        </Link>

        <Link to="/dashboard" className="feature-card">
          <div className="feature-icon">📈</div>
          <h3>Admin Dashboard</h3>
          <p>Occupancy metrics, ward status, and system analytics</p>
        </Link>
      </div>

      <div className="info-section">
        <h2>System Overview</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>Hospital Layout</strong>
            <p>
              20 beds arranged as 4 wards (ICU, GENERAL, SURGERY, MATERNITY)
              with 5 beds each
            </p>
          </div>
          <div className="info-item">
            <strong>Agent Types</strong>
            <p>
              8 specialized agents handling admission, assignment, discharge,
              cleaning, and resource management
            </p>
          </div>
          <div className="info-item">
            <strong>Smart Features</strong>
            <p>
              Severity scoring with Gemini AI, waiting list prioritization,
              emergency preemption, and auto-assignment
            </p>
          </div>
          <div className="info-item">
            <strong>Communication</strong>
            <p>
              Real-time message bubbles and Mermaid sequence diagrams
              visualizing agent interactions
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
