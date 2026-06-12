"""
AI Resume Analyzer — Frontend API Utilities

HTTP client wrapper for calling the FastAPI backend, plus
session state helpers for auth management.
"""

import httpx
import streamlit as st
from typing import Optional


API_BASE = "http://localhost:8000/api"


def get_headers() -> dict:
    """Get auth headers from session state."""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_get(path: str, params: dict = None) -> Optional[dict | list]:
    """Make a GET request to the backend API."""
    try:
        resp = httpx.get(
            f"{API_BASE}{path}",
            headers=get_headers(),
            params=params,
            timeout=30.0,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"API Error ({resp.status_code}): {resp.json().get('detail', resp.text)}")
            return None
    except httpx.ConnectError:
        st.error("⚠️ Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def api_post(path: str, json_data: dict = None, files: dict = None) -> Optional[dict]:
    """Make a POST request to the backend API."""
    try:
        kwargs = {
            "headers": get_headers(),
            "timeout": 60.0,
        }
        if files:
            # Remove Content-Type from headers for multipart
            headers = get_headers()
            kwargs["headers"] = headers
            kwargs["files"] = files
        elif json_data is not None:
            kwargs["json"] = json_data

        resp = httpx.post(f"{API_BASE}{path}", **kwargs)

        if resp.status_code in (200, 201):
            return resp.json()
        else:
            detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            st.error(f"API Error ({resp.status_code}): {detail}")
            return None
    except httpx.ConnectError:
        st.error("⚠️ Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def api_put(path: str, json_data: dict) -> Optional[dict]:
    """Make a PUT request to the backend API."""
    try:
        resp = httpx.put(
            f"{API_BASE}{path}",
            headers=get_headers(),
            json=json_data,
            timeout=30.0,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"API Error ({resp.status_code}): {resp.json().get('detail', resp.text)}")
            return None
    except httpx.ConnectError:
        st.error("⚠️ Cannot connect to backend.")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def api_delete(path: str) -> Optional[dict]:
    """Make a DELETE request to the backend API."""
    try:
        resp = httpx.delete(
            f"{API_BASE}{path}",
            headers=get_headers(),
            timeout=30.0,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"API Error ({resp.status_code}): {resp.json().get('detail', resp.text)}")
            return None
    except httpx.ConnectError:
        st.error("⚠️ Cannot connect to backend.")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def login(username: str, password: str) -> bool:
    """Authenticate and store token in session."""
    result = api_post("/auth/login", {"username": username, "password": password})
    if result and "access_token" in result:
        st.session_state["token"] = result["access_token"]
        # Fetch user profile
        me = api_get("/auth/me")
        if me:
            st.session_state["user"] = me
            return True
    return False


def register(username: str, email: str, password: str, role: str, full_name: str = "") -> bool:
    """Register a new user."""
    result = api_post("/auth/register", {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
        "full_name": full_name or username,
    })
    return result is not None


def logout():
    """Clear session state."""
    for key in ["token", "user"]:
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    """Check if user is authenticated."""
    return "token" in st.session_state and "user" in st.session_state


def is_admin() -> bool:
    """Check if current user is admin."""
    user = st.session_state.get("user", {})
    return user.get("role") == "admin"


def get_user() -> dict:
    """Get current user info."""
    return st.session_state.get("user", {})
