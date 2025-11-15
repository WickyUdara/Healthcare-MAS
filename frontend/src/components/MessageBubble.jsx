import React from "react";
import "./MessageBubble.css";

export default function MessageBubble({ message }) {
  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const performativeColors = {
    request: "#2196F3",
    inform: "#4CAF50",
    propose: "#FF9800",
    accept: "#4CAF50",
    reject: "#F44336",
    query: "#9C27B0",
  };

  return (
    <div className="message-bubble">
      <div className="message-header">
        <strong>{message.sender}</strong>
        <span className="message-arrow">→</span>
        <strong>{message.receiver}</strong>
      </div>
      <div
        className="message-performative"
        style={{
          backgroundColor: performativeColors[message.performative] || "#999",
        }}
      >
        {message.performative.toUpperCase()}
      </div>
      {message.reason && <div className="message-reason">{message.reason}</div>}
      <div className="message-timestamp">{formatTime(message.timestamp)}</div>
    </div>
  );
}
