from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class FetchResult:
    status: str              # "ok" | "error"
    response: Optional[Any] = None
    error: Optional[str] = None


