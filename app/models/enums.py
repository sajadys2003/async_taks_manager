import enum

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# class UserRole(str, enum.Enum):
#     USER = "user"
#     ADMIN = "admin"
