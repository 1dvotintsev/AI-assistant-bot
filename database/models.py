from sqlalchemy import String, Text, BigInteger, ForeignKey, Boolean, Integer, Numeric, func, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Models(Base):
    __tablename__ = 'models'
    
    model_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)


class UsersModels(Base):
    __tablename__ = 'users_models'
    
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    model_name: Mapped[str] = mapped_column(String, ForeignKey("models.model_name", ondelete="CASCADE"), primary_key=True)
    
    
class Datasets(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    format: Mapped[str | None] = mapped_column(String(50))
    size: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str | None] = mapped_column(String(50))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    
class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_cnt: Mapped[int] = mapped_column(Integer, default=0)
    model_cnt: Mapped[int] = mapped_column(Integer, default=0)
    balance: Mapped[float] = mapped_column(Numeric(15, 4), default=0.0000)
    
    
class UsersDatasets(Base):
    __tablename__ = "users_datasets"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String, ForeignKey("datasets.dataset_id", ondelete="CASCADE"), primary_key=True)
    
    
class Transactions(Base):
    __tablename__ = "transactions"

    hash: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("type IN ('deposit', 'withdraw')", name="check_transaction_type"),
    )