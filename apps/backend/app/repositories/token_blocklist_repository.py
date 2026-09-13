"""Repository operations for revoked access-token identifiers."""

from sqlalchemy.dialects.postgresql import insert

from app.extensions import db
from app.models.token_blocklist import TokenBlocklist


class TokenBlocklistRepository:
    """Keep access-token revocation persistence out of HTTP and service code."""

    @staticmethod
    def is_revoked(jti: str) -> bool:
        """Return whether the given JWT identifier has been explicitly revoked."""

        return (
            db.session.query(TokenBlocklist.id)
            .filter(TokenBlocklist.jti == jti)
            .first()
            is not None
        )

    @staticmethod
    def create_if_absent(
        *,
        jti: str,
        user_id: str,
        token_type: str,
        expires_at,
        commit: bool = True,
    ) -> None:
        """Stage unique revocation metadata and optionally commit it immediately.

        Callers coordinating a larger security transaction pass ``commit=False``
        so this insertion is committed atomically with the other mutations.
        """

        statement = (
            insert(TokenBlocklist)
            .values(
                jti=jti,
                user_id=user_id,
                token_type=token_type,
                expires_at=expires_at,
            )
            .on_conflict_do_nothing(index_elements=[TokenBlocklist.jti])
        )
        db.session.execute(statement)
        if commit:
            db.session.commit()
