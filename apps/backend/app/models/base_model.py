from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.extensions import db

class BaseModel(db.Model):
    """Shared persistence base for CADRI database entities.

    This abstract model centralizes the columns and helpers that every
    table-backed entity in the application can reuse: a UUID primary key,
    creation and update timestamps, a convenience persistence method, and a
    JSON-friendly serializer.
    """

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
        """Persist the current instance in the active database session.

        This keeps service and repository code focused on business rules instead
        of repeating the same add/commit sequence for every model instance.
        """

        db.session.add(self)
        db.session.commit()

    def update_timestamp(self) -> None:
        """Refresh the update timestamp and persist the new value immediately.

        The in-memory value is updated explicitly so the object state stays in
        sync with the timestamp that will be stored in the database.
        """

        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()

    def to_dict(self) -> dict:
        """Serialize the model into JSON-friendly primitives.

        Datetime values are converted to ISO 8601 strings and UUID values are
        stringified so API responses remain stable and easy to consume.
        """

        result = {}

        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Normalize non-JSON-native values before exposing them through APIs.
            if hasattr(value, "isoformat"):
                result[column.name] = value.isoformat()

            elif column.name == "id" and value is not None:
                result[column.name] = str(value)

            else:
                result[column.name] = value

        return result
