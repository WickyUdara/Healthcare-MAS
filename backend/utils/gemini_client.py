"""
Gemini API client for severity scoring and explanations.
Falls back to deterministic functions if GEMINI_API_KEY not provided.
"""

import os
import json
from typing import Dict, Any, Optional, Tuple

# Try to import Gemini client; fallback gracefully if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Using fallback severity scoring.")


class GeminiClient:
    """
    Client for interacting with Google Gemini API.
    Falls back to deterministic scoring if API key is missing or API unavailable.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key. If None, falls back to deterministic functions.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.use_gemini = self.api_key and GEMINI_AVAILABLE
        
        if self.use_gemini:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                print("✓ Gemini API initialized successfully")
            except Exception as e:
                print(f"⚠️  Failed to initialize Gemini: {e}. Using fallback.")
                self.use_gemini = False
    
    def score_severity(self, patient: Dict[str, Any]) -> Tuple[float, str]:
        """
        Score patient severity using Gemini (or fallback deterministic function).
        
        Args:
            patient: Patient data dict with keys: age, symptoms, heart_rate, blood_pressure, 
                    oxygen_saturation, is_emergency
        
        Returns:
            Tuple of (severity_score: float [0-100], explanation: str)
        """
        if self.use_gemini:
            return self._score_severity_gemini(patient)
        else:
            return self._score_severity_fallback(patient)
    
    def _score_severity_gemini(self, patient: Dict[str, Any]) -> Tuple[float, str]:
        """
        Call Gemini to generate severity score.
        """
        try:
            symptoms = patient.get("symptoms", "")
            heart_rate = patient.get("heart_rate", 80)
            bp = patient.get("blood_pressure", "120/80")
            o2 = patient.get("oxygen_saturation", 98)
            age = patient.get("age", 50)
            is_emergency = patient.get("is_emergency", False)
            
            prompt = f"""You are a medical severity assessment AI. Rate the following patient's condition severity (0-100).

Patient Details:
- Age: {age}
- Symptoms: {symptoms}
- Heart Rate: {heart_rate} bpm
- Blood Pressure: {bp}
- Oxygen Saturation: {o2}%
- Emergency: {is_emergency}

Respond ONLY with JSON (no markdown, no backticks):
{{"score": <int 0-100>, "reason": "<one sentence explanation>"}}

Score guidelines:
- 0-20: Stable, minor issues
- 21-40: Moderate, manageable issues
- 41-60: Significant concern, needs attention
- 61-80: Serious, urgent care needed
- 81-100: Critical, life-threatening"""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response (remove markdown code blocks if present)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            score = float(result.get("score", 50))
            reason = result.get("reason", "Assessment completed")
            
            # Clamp score to 0-100
            score = max(0, min(100, score))
            return score, reason
            
        except Exception as e:
            print(f"⚠️  Gemini call failed: {e}. Using fallback.")
            return self._score_severity_fallback(patient)
    
    def _score_severity_fallback(self, patient: Dict[str, Any]) -> Tuple[float, str]:
        """
        Deterministic severity scoring without API call.
        Weighted calculation based on vital signs and symptoms.
        """
        score = 0
        reasons = []
        
        age = patient.get("age", 50)
        symptoms = patient.get("symptoms", "").lower()
        heart_rate = patient.get("heart_rate", 80)
        bp = patient.get("blood_pressure", "120/80")
        o2 = patient.get("oxygen_saturation", 98)
        is_emergency = patient.get("is_emergency", False)
        
        # Age factor
        if age > 75:
            score += 15
            reasons.append("Advanced age (>75)")
        elif age > 65:
            score += 10
            reasons.append("Senior age (>65)")
        
        # Emergency flag
        if is_emergency:
            score += 25
            reasons.append("Emergency flag set")
        
        # Heart rate analysis
        if heart_rate < 60 or heart_rate > 100:
            score += 15
            reasons.append(f"Abnormal HR ({heart_rate})")
        
        # Blood pressure parsing
        try:
            systolic = int(bp.split("/")[0])
            diastolic = int(bp.split("/")[1])
            if systolic > 160 or diastolic > 100:
                score += 20
                reasons.append(f"Elevated BP ({bp})")
            elif systolic < 90 or diastolic < 60:
                score += 15
                reasons.append(f"Low BP ({bp})")
        except:
            pass
        
        # Oxygen saturation
        if o2 < 95:
            score += 20
            reasons.append(f"Low O2 ({o2}%)")
        
        # Symptom analysis
        critical_keywords = ["chest pain", "stroke", "hemorrhage", "respiratory failure", "cardiac"]
        serious_keywords = ["acute", "severe", "critical", "emergency"]
        moderate_keywords = ["pain", "fever", "infection", "broken", "fracture"]
        
        for keyword in critical_keywords:
            if keyword in symptoms:
                score += 30
                reasons.append(f"Critical symptom: {keyword}")
                break
        else:
            for keyword in serious_keywords:
                if keyword in symptoms:
                    score += 15
                    reasons.append(f"Serious symptom: {keyword}")
                    break
            else:
                for keyword in moderate_keywords:
                    if keyword in symptoms:
                        score += 5
                        reasons.append(f"Moderate concern: {keyword}")
        
        # Clamp score to 0-100
        final_score = max(0, min(100, score))
        reason = " | ".join(reasons) if reasons else "Stable patient"
        
        return final_score, reason
    
    def explain_assignment(self, bundle: Dict[str, Any]) -> str:
        """
        Generate human-friendly explanation for bed assignment.
        
        Args:
            bundle: Dict with keys: patient_name, bed_number, ward_name, reason
        
        Returns:
            Human-readable explanation string
        """
        if self.use_gemini:
            return self._explain_assignment_gemini(bundle)
        else:
            return self._explain_assignment_fallback(bundle)
    
    def _explain_assignment_gemini(self, bundle: Dict[str, Any]) -> str:
        """
        Use Gemini to generate a natural language explanation.
        """
        try:
            patient_name = bundle.get("patient_name", "Patient")
            bed_number = bundle.get("bed_number", "unknown")
            ward_name = bundle.get("ward_name", "unknown")
            severity = bundle.get("severity", 50)
            symptoms = bundle.get("symptoms", "")
            
            prompt = f"""Provide a brief (one sentence) explanation for this hospital bed assignment.

Patient: {patient_name}
Severity: {severity}/100
Symptoms: {symptoms}
Assigned Bed: {bed_number} in {ward_name} ward

Respond with only the explanation, no additional text."""

            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️  Gemini explanation failed: {e}")
            return self._explain_assignment_fallback(bundle)
    
    def _explain_assignment_fallback(self, bundle: Dict[str, Any]) -> str:
        """
        Fallback template-based explanation.
        """
        patient_name = bundle.get("patient_name", "Patient")
        bed_number = bundle.get("bed_number", "unknown")
        ward_name = bundle.get("ward_name", "unknown")
        severity = bundle.get("severity", 50)
        
        if severity > 70:
            template = f"{patient_name} assigned to {bed_number} ({ward_name}) for critical care."
        elif severity > 40:
            template = f"{patient_name} assigned to {bed_number} ({ward_name}) for monitoring."
        else:
            template = f"{patient_name} assigned to {bed_number} ({ward_name}) for standard care."
        
        return template


# Singleton instance
_gemini_client = None


def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
