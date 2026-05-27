from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.extensions import db

class BaseModel(db.Model):
    """Common base model shared by all database entities."""

    __abstract__ = True

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def save(self) -> None:
        """Persist the current instance in the active database session."""

        db.session.add(self)
        db.session.commit()

    def update_timestamp(self) -> None:
        """Refresh the in-memory update timestamp and persist the change."""

        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()

    def to_dict(self) -> dict:
        """Serialize the model into JSON-friendly primitives."""

        result = {}

        for column in self.__table__.columns:
            value = getattr(self, column.name)

            if hasattr(value, "isoformat"):
                result[column.name] = value.isoformat()

            elif column.name == "id" and value is not None:
                result[column.name] = str(value)

            else:
                result[column.name] = value

        return result
