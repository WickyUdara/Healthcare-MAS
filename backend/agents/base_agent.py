"""
Base agent class defining the interface and common functionality for all agents.
"""

import json
import os
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.message_schema import Message, Performative


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the MAS.
    Provides common messaging, logging, and action framework.
    """
    
    def __init__(self, name: str, db_session=None, activity_log_file: str = "activity_log.json"):
        """
        Initialize base agent.
        
        Args:
            name: Agent name (e.g., "AdmissionAgent")
            db_session: SQLAlchemy session for database operations
            activity_log_file: Path to activity log JSON file
        """
        self.name = name
        self.db_session = db_session
        self.activity_log_file = activity_log_file
        self.inbox = []  # Received messages
        self.outbox = []  # Messages to send
        print(f"[OK] {name} initialized")
    
    def send(self, message: Message) -> None:
        """
        Send a message to another agent.
        - Appends to activity log
        - Stores in outbox
        - Persists to database if session available
        
        This is where agent communication is recorded for visualization.
        
        Args:
            message: Message object following FIPA format
        """
        # Add to outbox
        self.outbox.append(message.dict())
        
        # Persist to activity log JSON file
        try:
            activity_log = []
            if os.path.exists(self.activity_log_file):
                with open(self.activity_log_file, "r") as f:
                    activity_log = json.load(f)
            
            activity_log.append({
                "id": message.id,
                "transaction_id": message.transaction_id,
                "timestamp": message.timestamp,
                "sender": message.sender,
                "receiver": message.receiver,
                "performative": message.performative,
                "content": message.content,
                "reason": message.reason,
            })
            
            with open(self.activity_log_file, "w") as f:
                json.dump(activity_log, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to write activity log: {e}")
        
        # Persist to database if available
        if self.db_session:
            try:
                from db.models import ActivityLog
                log_entry = ActivityLog(
                    message_id=message.id,
                    transaction_id=message.transaction_id,
                    timestamp=datetime.fromisoformat(message.timestamp),
                    sender=message.sender,
                    receiver=message.receiver,
                    performative=message.performative,
                    content=json.dumps(message.content),
                    reason=message.reason,
                )
                self.db_session.add(log_entry)
                self.db_session.commit()
            except Exception as e:
                print(f"⚠️  Failed to persist message to DB: {e}")
    
    def receive(self, message: Message) -> None:
        """
        Receive a message from another agent.
        
        Args:
            message: Message object
        """
        self.inbox.append(message.dict())
        print(f"  [{self.name}] received {message.performative} from {message.sender}")
    
    def create_message(
        self,
        transaction_id: str,
        performative: Performative,
        receiver: str,
        content: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> Message:
        """
        Create and format a FIPA-like message.
        
        Args:
            transaction_id: Transaction ID (groups related messages)
            performative: Message type (request, inform, propose, accept, reject, query)
            receiver: Recipient agent name
            content: Message payload
            reason: Optional human-readable explanation
        
        Returns:
            Message object
        """
        return Message(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            transaction_id=transaction_id,
            performative=performative.value if isinstance(performative, Performative) else performative,
            sender=self.name,
            receiver=receiver,
            content=content,
            reason=reason,
        )
    
    @abstractmethod
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent action method - must be implemented by subclasses.
        
        Args:
            state: Shared system state (patients, beds, waiting list, etc.)
        
        Returns:
            Updated state after agent action
        """
        pass
