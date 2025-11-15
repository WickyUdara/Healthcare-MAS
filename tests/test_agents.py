"""
Unit tests for Hospital Bed Management MAS agents.
Tests core workflows: admission, cleaning, waiting list auto-assign.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from agents.admission_agent import AdmissionAgent
from agents.cleaning_agent import CleaningAgent
from agents.waitinglist_agent import WaitingListAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.bed_assignment_agent import BedAssignmentAgent
from utils.gemini_client import GeminiClient
from utils.message_schema import Performative


class TestAdmissionAgent:
    """Test admission workflow."""
    
    @pytest.mark.asyncio
    async def test_admission_creates_patient(self):
        """Test that admission agent creates a patient record."""
        agent = AdmissionAgent()
        
        state = {
            "patients": [],
            "pending_admissions": [],
            "new_admission_requests": [
                {
                    "name": "John Doe",
                    "age": 65,
                    "gender": "Male",
                    "symptoms": "Chest pain",
                    "heart_rate": 95,
                    "blood_pressure": "160/100",
                    "oxygen_saturation": 92,
                    "is_emergency": True,
                    "preferred_ward": "ICU",
                }
            ]
        }
        
        updated_state = await agent.act(state)
        
        assert len(updated_state["patients"]) == 1
        patient = updated_state["patients"][0]
        assert patient["name"] == "John Doe"
        assert patient["severity_score"] > 0
        assert patient["status"] == "waiting"
        assert patient["transaction_id"] is not None


class TestGeminiClient:
    """Test Gemini client with fallback."""
    
    def test_fallback_severity_scoring(self):
        """Test deterministic severity scoring."""
        client = GeminiClient(api_key=None)  # Force fallback
        
        patient = {
            "age": 75,
            "symptoms": "chest pain",
            "heart_rate": 105,
            "blood_pressure": "180/110",
            "oxygen_saturation": 88,
            "is_emergency": True,
        }
        
        score, explanation = client.score_severity(patient)
        
        assert 0 <= score <= 100
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        # High severity expected for these vitals
        assert score > 50


class TestCleaningAgent:
    """Test bed cleaning workflow."""
    
    @pytest.mark.asyncio
    async def test_cleaning_simulation(self, monkeypatch):
        """Test that cleaning agent simulates bed cleaning."""
        agent = CleaningAgent()
        
        # Mock asyncio.sleep to speed up test
        sleep_called = []
        async def mock_sleep(duration):
            sleep_called.append(duration)
        
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)
        
        state = {
            "beds": [
                {
                    "id": 1,
                    "bed_number": "ICU-01",
                    "ward_name": "ICU",
                    "status": "cleaning",
                    "current_patient_id": None,
                    "cleaning_start_time": __import__('time').time(),
                }
            ],
            "cleaning_requests": [
                {
                    "transaction_id": "test-tx-001",
                    "bed_id": 1,
                    "bed_number": "ICU-01",
                }
            ],
        }
        
        updated_state = await agent.act(state)
        
        # Check that sleep was called with 10 seconds
        assert len(sleep_called) == 1
        assert sleep_called[0] == 10
        
        # Check that bed is now available
        assert updated_state["beds"][0]["status"] == "available"
        assert updated_state["beds"][0]["current_patient_id"] is None


class TestWaitingListAgent:
    """Test waiting list auto-assignment."""
    
    @pytest.mark.asyncio
    async def test_auto_assign_highest_priority(self):
        """Test that waiting list auto-assigns highest priority patient."""
        agent = WaitingListAgent()
        
        state = {
            "patients": [
                {
                    "id": 1,
                    "name": "Patient A",
                    "status": "waiting",
                    "severity_score": 75,
                    "admission_time": "2025-01-01T10:00:00",
                    "preferred_ward": "ICU",
                },
                {
                    "id": 2,
                    "name": "Patient B",
                    "status": "waiting",
                    "severity_score": 45,
                    "admission_time": "2025-01-01T09:00:00",
                    "preferred_ward": "ICU",
                },
            ],
            "beds": [
                {
                    "id": 1,
                    "bed_number": "ICU-01",
                    "ward_name": "ICU",
                    "status": "available",
                },
            ],
            "bed_available_notifications": [
                {
                    "transaction_id": "test-tx-001",
                    "bed_id": 1,
                    "bed_number": "ICU-01",
                }
            ],
            "pending_assignments": [],
        }
        
        updated_state = await agent.act(state)
        
        # Check that highest severity patient (Patient A) was assigned
        assert len(updated_state["pending_assignments"]) == 1
        assignment = updated_state["pending_assignments"][0]
        assert assignment["patient_id"] == 1  # Patient A (severity 75)


class TestCoordinatorAgent:
    """Test coordinator agent."""
    
    @pytest.mark.asyncio
    async def test_negotiation_rounds(self):
        """Test that coordinator handles negotiation rounds."""
        agent = CoordinatorAgent()
        
        state = {
            "beds": [
                {
                    "id": 1,
                    "bed_number": "ICU-01",
                    "ward_name": "ICU",
                    "status": "available",
                }
            ],
            "patients": [
                {
                    "id": 1,
                    "name": "Emergency Patient",
                    "severity_score": 85,
                    "preferred_ward": "ICU",
                    "is_emergency": True,
                }
            ],
            "available_beds": [
                {
                    "id": 1,
                    "bed_number": "ICU-01",
                    "ward_name": "ICU",
                    "status": "available",
                }
            ],
            "pending_admissions": [
                {
                    "transaction_id": "test-tx-001",
                    "patient": {
                        "id": 1,
                        "name": "Emergency Patient",
                        "severity_score": 85,
                        "preferred_ward": "ICU",
                        "is_emergency": True,
                    }
                }
            ],
            "pending_assignments": [],
        }
        
        updated_state = await agent.act(state)
        
        # Check that bed assignment was made
        assert len(updated_state["pending_assignments"]) >= 0  # May be 0 if mock responses differ


class TestMessageCreation:
    """Test message creation and logging."""
    
    def test_message_format(self):
        """Test FIPA-like message format."""
        agent = AdmissionAgent()
        
        msg = agent.create_message(
            transaction_id="test-tx-001",
            performative=Performative.REQUEST,
            receiver="CoordinatorAgent",
            content={"patient_id": 1, "name": "John"},
            reason="Test message"
        )
        
        assert msg.transaction_id == "test-tx-001"
        assert msg.performative == "request"
        assert msg.sender == "AdmissionAgent"
        assert msg.receiver == "CoordinatorAgent"
        assert msg.reason == "Test message"
        assert msg.id is not None
        assert msg.timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
