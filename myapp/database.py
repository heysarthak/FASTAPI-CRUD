import databases
import sqlalchemy
from config import config

metadata = sqlalchemy.MetaData()

user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("confirmed", sqlalchemy.Boolean, default=False)
)

tasks = sqlalchemy.Table(
    "tasks",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.Integer),
    sqlalchemy.Column("end_date", sqlalchemy.DATETIME),
    sqlalchemy.Column("owner_id", sqlalchemy.ForeignKey("users.id"), nullable=False),
    sqlalchemy.CheckConstraint("status IN (0, 1, 2)", name="status_check"),
    sqlalchemy.Index("idx_owner_status", "owner_id", "status")
)

engine = sqlalchemy.create_engine(
    config.DATABASE_URL, connect_args={"check_same_thread": False}
)

metadata.create_all(engine)
database = databases.Database(
    config.DATABASE_URL, force_rollback=config.DB_FORCE_ROLL_BACK
)