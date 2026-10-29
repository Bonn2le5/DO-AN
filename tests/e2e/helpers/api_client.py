"""
API Client & Network Discovery helper for E2E tests.
Provides unified HTTP request methods with live server detection and fallback.
"""

import os
from typing import Dict, Any, Optional
import requests


DEFAULT_BASE_URL = os.environ.get("MOC_BACKEND_URL", "http://127.0.0.1:8000")


class MocApiClient:
    """
    Client for interacting with the Nhà hàng Mộc backend REST & WebSocket endpoints.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 3.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.access_token: Optional[str] = None

    def is_backend_alive(self) -> bool:
        """Check if live backend server is reachable."""
        try:
            resp = self.session.get(f"{self.base_url}/api/", timeout=self.timeout)
            return resp.status_code in (200, 401, 403, 404)
        except Exception:
            return False

    def set_token(self, token: str):
        self.access_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        self.access_token = None
        self.session.headers.pop("Authorization", None)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self.session.get(url, params=params, timeout=self.timeout)

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self.session.post(url, json=json, timeout=self.timeout)

    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self.session.put(url, json=json, timeout=self.timeout)

    def patch(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self.session.patch(url, json=json, timeout=self.timeout)

    def delete(self, endpoint: str) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self.session.delete(url, timeout=self.timeout)
