# dummy_app.py
# Simulated dummy user management app for MCP demo

import logging

logger = logging.getLogger("dummy_app")

class MockApp:
    def __init__(self):
        self.users: dict[str, dict] = {}

    def create_user(self, user_id: str, name: str) -> dict:
        """Simulate creating a new user."""
        user = {"user_id": user_id, "name": name}
        self.users[user_id] = user
        logger.info(f"create_user: {user} | total_users={len(self.users)}")
        return user

    def get_user(self, user_id: str) -> dict:
        """Simulate retrieving user data."""
        user = self.users.get(user_id, {"error": "User not found"})
        logger.info(f"get_user: user_id={user_id} | result={user}")
        return user
