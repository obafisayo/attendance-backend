from sqlalchemy import Column, String, DateTime, func

from app.database import Base


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    jti = Column(String(255), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    blocked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
