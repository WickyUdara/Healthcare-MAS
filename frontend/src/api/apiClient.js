import axios from "axios";

// Use relative URL or environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.message);
    if (error.response) {
      console.error("Status:", error.response.status);
      console.error("Data:", error.response.data);
    }
    return Promise.reject(error);
  }
);

// Admission
export const admitPatient = (data) => apiClient.post("/admit", data);

// Discharge
export const dischargePatient = (patientId) =>
  apiClient.post(`/discharge/${patientId}`);

// Beds
export const getBeds = () => apiClient.get("/beds");

// Patients
export const getPatients = () => apiClient.get("/patients");

// Waiting List
export const getWaitingList = () => apiClient.get("/waiting_list");

// Activity Log
export const getActivityLog = (limit = 50) =>
  apiClient.get(`/activity_log?limit=${limit}`);

// Sequence Diagram
export const getSequenceDiagram = (transactionId) =>
  apiClient.get(`/sequence_diagram/${transactionId}`);

// Metrics
export const getMetrics = () => apiClient.get("/metrics");

// Config
export const getConfig = () => apiClient.get("/config");

// Health
export const healthCheck = () => apiClient.get("/health");

// Run assignment cycle (debug)
export const runAssignmentCycle = () => apiClient.post("/run_assignment_cycle");

export default apiClient;
