from flask import Blueprint, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from database.connection import engine

auth = Blueprint("auth", __name__)


@auth.route("/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        role = data.get("role")

        if not username or not password or not role:
            return {
                "status": "error",
                "message": "Username, password and role are required"
            }, 400

        if role not in ["owner", "vendor"]:
            return {
                "status": "error",
                "message": "Role must be owner or vendor"
            }, 400

        password_hash = generate_password_hash(password)

        query = text("""
            INSERT INTO users (username, password_hash, role)
            VALUES (:username, :password_hash, :role)
        """)

        with engine.begin() as connection:
            connection.execute(
                query,
                {
                    "username": username,
                    "password_hash": password_hash,
                    "role": role
                }
            )

        return {
            "status": "success",
            "message": "User registered successfully"
        }, 201

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500


@auth.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {
                "status": "error",
                "message": "Username and password are required"
            }, 400

        query = text("""
            SELECT id, username, password_hash, role, vendor_number
        FROM users
        WHERE username = :username
        """)

        with engine.connect() as connection:
            result = connection.execute(
                query,
                {"username": username}
            )
            user = result.mappings().first()

        if not user:
            return {
                "status": "error",
                "message": "Invalid username or password"
            }, 401

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            return {
                "status": "error",
                "message": "Invalid username or password"
            }, 401

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["vendor_number"] = user["vendor_number"]

        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"]
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500


@auth.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()

    return {
        "status": "success",
        "message": "Logout successful"
    }
from app.auth import login_required, role_required


@auth.route("/auth/test")
@login_required
def auth_test():
    return {
        "status": "success",
        "message": "You are logged in",
        "username": session.get("username"),
        "role": session.get("role")
    }


@auth.route("/auth/owner-test")
@role_required("owner")
def owner_test():
    return {
        "status": "success",
        "message": "Owner access granted",
        "username": session.get("username"),
        "role": session.get("role")
    }
    
@auth.route("/auth/me")
@login_required
def current_user():
    query = text("""
        SELECT username, role, vendor_number
        FROM users
        WHERE id = :user_id
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"user_id": session.get("user_id")}
        )
        user = result.mappings().first()

    return {
        "status": "success",
        "user": {
            "username": user["username"],
            "role": user["role"],
            "vendor_number": user["vendor_number"]
        }
    }