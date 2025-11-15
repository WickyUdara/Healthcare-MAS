import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

console.log("🚀 Starting React app...");

const root = ReactDOM.createRoot(document.getElementById("root"));
console.log("✓ Root element found and created");

try {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  console.log("✓ React app rendered");
} catch (err) {
  console.error("❌ React rendering error:", err);
  root.render(
    <div style={{ padding: "20px", color: "red", fontFamily: "Arial" }}>
      <h1>Error Loading App</h1>
      <p>{err.message}</p>
      <pre>{err.stack}</pre>
    </div>
  );
}
