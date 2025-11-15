import React from "react";

export default function DebugApp() {
  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1 style={{ color: "blue" }}>🏥 Hospital MAS System</h1>
      <p>Frontend is working!</p>
      <button onClick={() => alert("Button works!")}>Test Button</button>
    </div>
  );
}
