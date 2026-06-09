import enum

class UserRole(enum.Enum):
    admin = "admin"
    member = "member"

class ActionType(enum.Enum):
    borrow = "borrow"
    return_ = "return"

class MessageRole(enum.Enum):
    user      = "user"
    assistant = "assistant"
    system    = "system"

class ActionStatus(enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    executed  = "executed"