from sqlalchemy import String, Text, BigInteger, ForeignKey, Boolean, Integer, Numeric, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from decimal import Decimal

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
    
    
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC
from sqlalchemy import SmallInteger, TIMESTAMP

class Datasets(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int]    = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str]       = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    format: Mapped[str | None]      = mapped_column(String(50))
    size: Mapped[int | None]        = mapped_column(BigInteger)
    status: Mapped[str | None]      = mapped_column(String(50))
    is_public: Mapped[bool]         = mapped_column(Boolean, default=False)

    # новые поля 👇
    labels: Mapped[dict | None]     = mapped_column(JSONB)
    annotations_per_task: Mapped[int] = mapped_column(SmallInteger, default=3)
    reward_pool: Mapped[float]      = mapped_column(NUMERIC(15, 4), default=0.0000)
    closed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False))
    
    
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


# ------------------------------------------------------------
#  datasets <1——N> dataset_files
# ------------------------------------------------------------
class DatasetFiles(Base):
    __tablename__ = "dataset_files"

    file_id:   Mapped[int]  = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(Text, ForeignKey("datasets.dataset_id", ondelete="CASCADE"), index=True)
    uri:        Mapped[str] = mapped_column(Text, nullable=False)      # tg://..., s3://...
    original_name: Mapped[str | None] = mapped_column(Text)
    size:       Mapped[int | None]    = mapped_column(BigInteger)
    checksum:   Mapped[str | None]    = mapped_column(String(64))

# ------------------------------------------------------------
#  datasets <1——N> tasks  <1——N> annotations
# ------------------------------------------------------------
class Tasks(Base):
    __tablename__ = "tasks"

    task_id:    Mapped[int]  = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str]  = mapped_column(Text, ForeignKey("datasets.dataset_id", ondelete="CASCADE"), index=True)
    text_row:   Mapped[str]  = mapped_column(Text, nullable=False)
    status:     Mapped[str]  = mapped_column(String(10), default="new")
    annotated_cnt: Mapped[int] = mapped_column(Integer, default=0)


class Annotations(Base):
    __tablename__ = "annotations"

    annotation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id:  Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.task_id", ondelete="CASCADE"), index=True)
    user_id:  Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    label:    Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("task_id", "user_id", name="uq_task_user"),)


# ------------------------------------------------------------
#  tasks <1——1> task_results
# ------------------------------------------------------------
class TaskResults(Base):
    __tablename__ = "task_results"

    task_id:   Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.task_id", ondelete="CASCADE"), primary_key=True)
    final_label: Mapped[bool | None] = mapped_column(Boolean)
    confidence:  Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    closed_at:   Mapped[datetime | None] = mapped_column(TIMESTAMP)
