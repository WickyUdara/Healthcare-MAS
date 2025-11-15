import React, { useState, useEffect } from "react";
import { getActivityLog, getSequenceDiagram } from "../api/apiClient";
import MessageBubble from "../components/MessageBubble";
import SequenceDiagram from "../components/SequenceDiagram";
import "./AgentActivityLog.css";

export default function AgentActivityLog() {
  const [activityLog, setActivityLog] = useState([]);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [diagramData, setDiagramData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterAgent, setFilterAgent] = useState("");

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const res = await getActivityLog(100);
      setActivityLog(res.data);
    } catch (err) {
      console.error("Error fetching activity log:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTransaction = async (transactionId) => {
    if (selectedTransaction === transactionId) {
      setSelectedTransaction(null);
      setDiagramData(null);
      return;
    }

    try {
      const res = await getSequenceDiagram(transactionId);
      setDiagramData(res.data);
      setSelectedTransaction(transactionId);
    } catch (err) {
      console.error("Error fetching diagram:", err);
    }
  };

  if (loading)
    return (
      <div className="activity-log-page">
        <p>Loading...</p>
      </div>
    );

  // Get unique agents for filter
  const agents = [
    ...new Set(activityLog.flatMap((log) => [log.sender, log.receiver])),
  ].sort();

  // Filter logs
  const filteredLogs = filterAgent
    ? activityLog.filter(
        (log) => log.sender === filterAgent || log.receiver === filterAgent
      )
    : activityLog;

  // Group by transaction
  const transactionGroups = {};
  filteredLogs.forEach((log) => {
    if (!transactionGroups[log.transaction_id]) {
      transactionGroups[log.transaction_id] = [];
    }
    transactionGroups[log.transaction_id].push(log);
  });

  return (
    <div className="activity-log-page">
      <h1>📊 Agent Activity Log</h1>

      <div className="controls">
        <label>Filter by Agent:</label>
        <select
          value={filterAgent}
          onChange={(e) => setFilterAgent(e.target.value)}
        >
          <option value="">All Agents</option>
          {agents.map((agent) => (
            <option key={agent} value={agent}>
              {agent}
            </option>
          ))}
        </select>
      </div>

      <div className="content">
        <div className="transactions-panel">
          <h2>Transactions ({Object.keys(transactionGroups).length})</h2>
          <div className="transactions-list">
            {Object.entries(transactionGroups).map(([txId, messages]) => (
              <div
                key={txId}
                className={`transaction-item ${
                  selectedTransaction === txId ? "active" : ""
                }`}
                onClick={() => handleSelectTransaction(txId)}
              >
                <div className="tx-header">
                  <span className="tx-id">{txId.substring(0, 8)}</span>
                  <span className="tx-count">{messages.length} msgs</span>
                </div>
                <div className="tx-preview">
                  {messages[0]?.sender} → {messages[0]?.receiver}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="details-panel">
          {selectedTransaction ? (
            <>
              <h2>
                Transaction Details: {selectedTransaction.substring(0, 12)}
              </h2>

              {diagramData && (
                <SequenceDiagram
                  mermaidText={diagramData.mermaid_text}
                  title={`Agent Communication Flow`}
                />
              )}

              <div className="messages-section">
                <h3>Message Sequence</h3>
                {transactionGroups[selectedTransaction]?.map((msg, idx) => (
                  <div key={idx} className="message-wrapper">
                    <div className="message-number">{idx + 1}</div>
                    <MessageBubble message={msg} />
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>Select a transaction to view details and sequence diagram</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
