from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

from .database import Base


class MoneyType(TypeDecorator):
    """Keep exact money in PostgreSQL and avoid float rounding in SQLite tests."""

    impl = Numeric
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(64))
        return dialect.type_descriptor(Numeric(31, 2))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Store incoming values in an exact, database-safe representation.
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
        return format(decimal_value, "f") if dialect.name == "sqlite" else decimal_value

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, Decimal):
            return value
        return Decimal(str(value))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    categories = relationship("Category", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    budgets = relationship("Budget", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_categories_user"),
        nullable=False
    )

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name="uq_categories_user_name"
        ),
        Index("ix_categories_user_id", "user_id"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_transactions_user"),
        nullable=False
    )
    category_id = Column(
        Integer,
        ForeignKey("categories.id", name="fk_transactions_category"),
        nullable=False
    )
    amount = Column(MoneyType(), nullable=False)
    type = Column(String(20), nullable=False)
    description = Column(String(255), nullable=True)
    debt_direction = Column(String(20), nullable=True)
    interest_amount = Column(MoneyType(), nullable=True)
    investment_action = Column(String(20), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

    __table_args__ = (Index("ix_transactions_user_date", "user_id", "date"),)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_budgets_user"),
        nullable=False
    )
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount = Column(MoneyType(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "year",
            "month",
            name="uq_budgets_user_year_month"
        ),
        Index("ix_budgets_user_id", "user_id"),
    )
