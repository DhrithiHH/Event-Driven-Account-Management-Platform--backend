from dataclasses import dataclass
from uuid import UUID


@dataclass
class GetNotificationEventsQuery:
    user_id: UUID
