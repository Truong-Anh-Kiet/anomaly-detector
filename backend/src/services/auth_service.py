"""Authentication service for user management and JWT"""

import logging
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config import get_settings
from src.models import RoleEnum, User
from src.schemas.user import TokenPayload, UserCreate

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and user management service"""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(
        self, db: Session, user_create: UserCreate, role: RoleEnum = RoleEnum.ANALYST
    ) -> User:
        """Create a new user"""
        # Check if user exists
        existing_user = db.query(User).filter(User.username == user_create.username).first()
        if existing_user:
            raise ValueError(f"Username '{user_create.username}' already exists")

        # Create user with hashed password
        hashed_password = self.hash_password(user_create.password)
        db_user = User(
            username=user_create.username,
            password_hash=hashed_password,
            role=role,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"Created new user: {user_create.username} with role {role}")
        return db_user

    def authenticate_user(self, db: Session, username: str, password: str) -> User:
        """Authenticate user by username and password"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return user

    def create_access_token(self, user: User, expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        if expires_delta is None:
            expires_delta = timedelta(
                minutes=self.settings.jwt_access_token_expire_minutes
            )

        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": user.user_id,
            "role": user.role.value,
            "assigned_categories": user.assigned_categories or [],
            "exp": expire,
            "token_type": "access",
        }

        encoded_jwt = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        return encoded_jwt

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expires_delta = timedelta(days=self.settings.jwt_refresh_token_expire_days)
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": user.user_id,
            "exp": expire,
            "token_type": "refresh",
        }

        encoded_jwt = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        return encoded_jwt

    def verify_token(self, token: str) -> TokenPayload:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            token_payload = TokenPayload(**payload)
            return token_payload
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def get_user_from_token(self, db: Session, token: str) -> User:
        """Extract user from JWT token"""
        token_payload = self.verify_token(token)
        if not token_payload:
            return None

        user = db.query(User).filter(User.user_id == token_payload.sub).first()
        return user
