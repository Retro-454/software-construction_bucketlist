'''Flask api is to be called by php calls
each actor needs a X-Actor-Id with logged-in user's id
(a substitute for Auth issues real sessions)
ERRORS WILL BE MADE VIA JSON
{"error": "..."} with 400 status code
401(no actor) if no actor is provided
403 (not authorized) if actor is not allowed to do the action
404 if the resource is not found
'''

import sqlite3

from Bucket import Bucket
from Category import Category
from Db import Db
from Task import Task
from flask import Flask, jsonify, request, session, redirect
from werkzeug.security import check_password_hash
import os


class MissingActorError(Exception):
    pass  # 401


def create_app(db=None):
    if db is None:
        from database.init_DB import get_connection, init_db

        init_db()  # create the database if it does not exist yet
        db = Db(connect=get_connection)

    buckets = Bucket(db)
    categories = Category(db, buckets)
    tasks = Task(db, buckets)

    managers = {
        "buckets": buckets,
        "categories": categories,
        "tasks": tasks,
    }

    app = Flask(
        __name__,
        static_folder="../frontend",
        static_url_path=""
    )

    app.config.update(
        SECRET_KEY=os.environ["FLASK_SECRET_KEY"],
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    @app.get("/")
    def login_page():
       if "user_id" in session:
            return redirect("/dashboard")

       return app.send_static_file("login.html")
    
    @app.get("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return redirect("/")

        return app.send_static_file("index.html")

    @app.post("/api/login")
    def login():

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid request"}), 400

        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str) or not username.strip():
            return jsonify({"error": "Username is required"}), 400

        if not isinstance(password, str) or not password:
            return jsonify({"error": "Password is required"}), 400

        users = db.execute(
            "SELECT user_id, username, password_hash "
            "FROM users WHERE username = ?",
            (username.strip(),)
        )

        if not users or not check_password_hash(
            users[0]["password_hash"], password
        ):
            return jsonify({
                "error": "Invalid username or password"}), 401

        user = users[0]
        session.clear()
        session["user_id"] = user["user_id"]

        return jsonify({
            "message": "Login successful",
            "username": user["username"],
            "redirect": "/dashboard"
        })
        

    @app.post("/api/logout")
    def logout():
        session.clear()
        return jsonify({"message": "Logout successful", "redirect": "/"})
    

    # --helpers--

    def actor() -> int:
        # get actor from request headers
        user_id = session.get("user_id")

        if user_id is None:
            raise MissingActorError("You must log in first")

        return user_id

    def body() -> dict:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")

        return data

    def manager(resource: str):
        if resource not in managers:
            raise LookupError(f"Unknown manager '{resource}'")

        return managers[resource]

    # --errors--

    def error(status):
        return lambda e: (jsonify({"error": str(e)}), status)

    app.register_error_handler(MissingActorError, error(401))
    app.register_error_handler(ValueError, error(400))
    app.register_error_handler(sqlite3.IntegrityError, error(400))
    app.register_error_handler(PermissionError, error(403))
    app.register_error_handler(LookupError, error(404))

    # --generic crud--

    @app.post("/api/<resource>")
    def create_record(resource):
        return jsonify(
            {"id": manager(resource).create(body(), actor())}
        ), 201

    @app.get("/api/<resource>/<int:record_id>")
    def read_record(resource, record_id):
        return jsonify(
            manager(resource).read(record_id, actor())
        )

    @app.patch("/api/<resource>/<int:record_id>")
    def update_record(resource, record_id):
        return jsonify(
            {"updated": manager(resource).update(record_id, body(), actor())}
        )

    @app.delete("/api/<resource>/<int:record_id>")
    def delete_record(resource, record_id):
        return jsonify(
            {"deleted": manager(resource).delete(record_id, actor())}
        )

 # --user workspace / bucket navigation--

    @app.get("/api/users/me")
    def current_user():
        user_id = actor()
        users = db.execute(
            "SELECT user_id, username FROM users WHERE user_id = ?", (user_id,)
        )
        if not users:
            raise LookupError(f"user {user_id} not found")
        return jsonify(users[0])

    @app.get("/api/buckets/mine")
    def my_buckets():
        return jsonify(buckets.list_for_user(actor()))

    @app.get("/api/buckets/<int:bucket_id>/categories")
    def bucket_categories(bucket_id):
        return jsonify(categories.list_for_bucket(bucket_id, actor()))

    # --buckets--

    @app.post("/api/buckets/<int:bucket_id>/members")
    def add_member(bucket_id):
        data = body()

        ok = buckets.add_member(
            bucket_id,
            data.get("user_id"),
            data.get("role"),
            actor(),
        )

        return jsonify({"added": ok}), 201

    @app.get("/api/buckets/<int:bucket_id>/role/<int:user_id>")
    def get_member_role(bucket_id, user_id):

        # requesting user must be able to view the bucket
        if not buckets.has_permission(bucket_id, actor(), "view"):
            raise PermissionError(
                "only bucket members can see roles"
            )

        return jsonify(
            {"role": buckets.get_member_role(bucket_id, user_id)}
        )

    # --categories--

    @app.get("/api/categories/<int:category_id>/tasks")
    def category_tasks(category_id):

        sort = request.args.get("sort", "PRIORITY").upper()

        return jsonify(
            categories.list_tasks(
                category_id,
                sort,
                actor(),
            )
        )

    @app.get("/api/categories/<int:category_id>/progress")
    def category_progress(category_id):
        return jsonify(
            categories.get_progress(
                category_id,
                actor(),
            )
        )

    # --tasks--

    @app.post("/api/tasks/<int:task_id>/notes")
    def task_note(task_id):
        return jsonify(
            {
                "note": tasks.add_note(
                    task_id,
                    body().get("text"),
                    actor(),
                )
            }
        ), 201

    @app.post("/api/tasks/<int:task_id>/subtasks")
    def task_subtask(task_id):
        return jsonify(
            {
                "id": tasks.add_subtask(
                    task_id,
                    body().get("title"),
                    actor(),
                )
            }
        ), 201

    @app.post("/api/tasks/<int:task_id>/complete")
    def task_complete(task_id):
        return jsonify(
            {
                "completed": tasks.complete_task(
                    task_id,
                    actor(),
                )
            }
        )

    return app


if __name__ == "__main__":
    create_app().run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )