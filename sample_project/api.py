"""REST API Endpoints and HTTP Request Routing."""

from typing import Dict, Any, List
from sample_project.auth import authenticate_user, verify_jwt_token
from sample_project.billing import process_order_checkout
from sample_project.database import DatabaseClient


class ApiRouter:
    """Mock HTTP REST router handling incoming requests and returning responses."""

    def __init__(self, db: DatabaseClient):
        self.db = db

    def handle_login_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v1/auth/login handler: authenticates user and returns token."""
        username = payload.get("username", "")
        password = payload.get("password", "")
        token = authenticate_user(self.db, username, password)
        if not token:
            return {"status_code": 401, "error": "Invalid username or password"}
        return {"status_code": 200, "token": token}

    def handle_checkout_request(self, auth_header: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v1/orders/checkout handler: verifies token and completes purchase."""
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"status_code": 401, "error": "Missing or malformed Authorization header"}

        raw_token = auth_header.replace("Bearer ", "").strip()
        user_info = verify_jwt_token(raw_token)
        if not user_info:
            return {"status_code": 403, "error": "Expired or invalid authorization token"}

        items = payload.get("items", [])
        coupon = payload.get("discount_code", "")
        order_summary = process_order_checkout(self.db, user_info["user_id"], items, coupon)
        return {"status_code": 201, "data": order_summary}

    def handle_get_profile(self, user_id: int) -> Dict[str, Any]:
        """GET /api/v1/users/{id} handler: fetch serialized user profile."""
        rows = self.db.execute_query(
            "SELECT id, username, email, role FROM users WHERE id = ?", (user_id,)
        )
        if not rows:
            return {"status_code": 404, "error": "User profile not found"}
        r = rows[0]
        return {
            "status_code": 200,
            "data": {"id": r[0], "username": r[1], "email": r[2], "role": r[3]},
        }
