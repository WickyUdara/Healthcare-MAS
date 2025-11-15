import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import "./App.css";

import Home from "./pages/Home";
import Admission from "./pages/Admission";
import BedAssignment from "./pages/BedAssignment";
import CleaningTurnaround from "./pages/CleaningTurnaround";
import Discharge from "./pages/Discharge";
import AgentActivityLog from "./pages/AgentActivityLog";
import Dashboard from "./pages/Dashboard";

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              🏥 Hospital MAS
            </Link>
            <ul className="nav-menu">
              <li className="nav-item">
                <Link to="/" className="nav-link">
                  Home
                </Link>
              </li>
              <li className="nav-item">
                <Link to="/admission" className="nav-link">
                  Admission
                </Link>
              </li>
              <li className="nav-item">
                <Link to="/bed-assignment" className="nav-link">
                  Beds
                </Link>
              </li>
              <li className="nav-item">
                <Link to="/cleaning" className="nav-link">
                  Cleaning
                </Link>
              </li>
              <li className="nav-item">
                <Link to="/discharge" className="nav-link">
                  Discharge
                </Link>
              </li>
              <li className="nav-item">
                <Link to="/activity-log" className="nav-link">
                  Activity Log
                </Link>
              </li>
              <li className="nav-item">
                <Link to="/dashboard" className="nav-link">
                  Dashboard
                </Link>
              </li>
            </ul>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/admission" element={<Admission />} />
            <Route path="/bed-assignment" element={<BedAssignment />} />
            <Route path="/cleaning" element={<CleaningTurnaround />} />
            <Route path="/discharge" element={<Discharge />} />
            <Route path="/activity-log" element={<AgentActivityLog />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>
            &copy; 2025 Hospital Multi-Agent System. Made for viva/demo
            purposes.
          </p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
