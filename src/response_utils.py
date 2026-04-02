from typing import Any, Dict


def ok(**kwargs: Any) -> Dict[str, Any]:
    payload = {"status": "success", "status_code": 200}
    payload.update(kwargs)
    return payload


def fail(status_code: int, message: str, **kwargs: Any) -> Dict[str, Any]:
    payload = {"status": "error", "status_code": status_code, "message": message}
    payload.update(kwargs)
    return payload
