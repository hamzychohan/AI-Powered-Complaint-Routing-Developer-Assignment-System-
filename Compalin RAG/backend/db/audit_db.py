# pyrefly: ignore [missing-import]
import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(100), nullable=False, index=True)
    developer = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=False)
    reasoning = Column(Text, nullable=False)
    jira_issue_key = Column(String(100), nullable=True)
    raw_inputs_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class AuditDB:
    def __init__(self, db_path: str = "./data/audit_logs.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def log_assignment(
        self,
        ticket_id: str,
        developer: str,
        priority: str,
        reasoning: str,
        jira_issue_key: Optional[str] = None,
        raw_inputs: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        session = self.SessionLocal()
        try:
            log_entry = AuditLog(
                ticket_id=ticket_id,
                developer=developer,
                priority=priority,
                reasoning=reasoning,
                jira_issue_key=jira_issue_key,
                raw_inputs_json=json.dumps(raw_inputs) if raw_inputs else None,
                timestamp=datetime.utcnow()
            )
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)
            return log_entry
        finally:
            session.close()

    def get_all_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        session = self.SessionLocal()
        try:
            logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
            result = []
            for log in logs:
                result.append({
                    "id": log.id,
                    "ticket_id": log.ticket_id,
                    "developer": log.developer,
                    "priority": log.priority,
                    "reasoning": log.reasoning,
                    "jira_issue_key": log.jira_issue_key,
                    "timestamp": log.timestamp.isoformat(),
                    "raw_inputs": json.loads(log.raw_inputs_json) if log.raw_inputs_json else None
                })
            return result
        finally:
            session.close()
