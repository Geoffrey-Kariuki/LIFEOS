# ============================================================
# LIFEOS - COMPLETE APP.PY
# ============================================================

import os
import sys

from flask import Flask, render_template, request, session, redirect, url_for
from database import db
from models import (
    User,
    Task,
    Goal,
    Memory,
    Transaction,
    CalendarEvent
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# ============================================================
# APP CONFIGURATION
# ============================================================

if getattr(sys, "frozen", False):

    # --------------------------------------------------------
    # PACKAGED EXE
    # --------------------------------------------------------

    BASE_DIR = sys._MEIPASS

    USER_DATA_DIR = os.path.join(
        os.environ.get(
            "LOCALAPPDATA",
            os.path.expanduser("~")
        ),
        "LIFEOS"
    )

else:

    # --------------------------------------------------------
    # NORMAL PYTHON / DEVELOPMENT
    # --------------------------------------------------------

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    USER_DATA_DIR = BASE_DIR


# ============================================================
# APPLICATION PATHS
# ============================================================

TEMPLATES_DIR = os.path.join(
    BASE_DIR,
    "templates"
)

STATIC_DIR = os.path.join(
    BASE_DIR,
    "static"
)

INSTANCE_DIR = os.path.join(
    USER_DATA_DIR,
    "instance"
)

os.makedirs(
    INSTANCE_DIR,
    exist_ok=True
)

DATABASE_PATH = os.path.join(
    INSTANCE_DIR,
    "lifeos.db"
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR
)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.environ.get(
    "LIFEOS_SECRET_KEY",
    "dev-only-secret-change-in-production"
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Render PostgreSQL
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

else:
    # Local development / Windows EXE
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + DATABASE_PATH.replace("\\", "/")
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ------------------------------------------------------------
# RENDER / POSTGRESQL
# ------------------------------------------------------------

if DATABASE_URL:

    # Some PostgreSQL providers may return the older
    # postgres:// format.
    #
    # SQLAlchemy expects postgresql://

    if DATABASE_URL.startswith("postgres://"):

        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL


# ------------------------------------------------------------
# LOCAL / EXE SQLITE
# ------------------------------------------------------------

else:

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///"
        + DATABASE_PATH.replace("\\", "/")
    )


app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False


# ============================================================
# INITIALIZE DATABASE
# ============================================================

db.init_app(app)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# HELPER - CURRENT USER
# ============================================================

def get_current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return None

    user = db.session.get(
        User,
        user_id
    )

    if user is None:

        session.pop(
            "user_id",
            None
        )

        return None

    return user


def login_required():

    return get_current_user()


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def home():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    tasks = Task.query.filter_by(
        user_id=user.id
    ).order_by(
        Task.id.desc()
    ).all()

    goals = Goal.query.filter_by(
        user_id=user.id
    ).order_by(
        Goal.id.desc()
    ).all()

    transactions = Transaction.query.filter_by(
        user_id=user.id
    ).all()

    income = sum(
        float(t.amount)
        for t in transactions
        if t.type == "income"
        or t.transaction_type == "income"
    )

    expenses = sum(
        float(t.amount)
        for t in transactions
        if t.type == "expense"
        or t.transaction_type == "expense"
    )

    balance = income - expenses

    return render_template(
        "index.html",
        user=user,
        tasks=tasks,
        task_count=len(tasks),
        goals=goals,
        goal_count=len(goals),
        income=income,
        expenses=expenses,
        balance=balance
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill in all fields."
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            return render_template(
                "register.html",
                error="An account with this email already exists."
            )

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(
                password
            )
        )

        db.session.add(
            new_user
        )

        db.session.commit()

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if session.get("user_id"):

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id

            return redirect(
                url_for("home")
            )

        return render_template(
            "login.html",
            error="Incorrect email or password."
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# TASKS
# ============================================================

@app.route(
    "/tasks",
    methods=["GET", "POST"]
)
def tasks():

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        if title:

            task = Task(
                title=title,
                completed=False,
                user_id=user.id
            )

            db.session.add(
                task
            )

            db.session.commit()

        return redirect(
            url_for("tasks")
        )

    tasks_list = Task.query.filter_by(
        user_id=user.id
    ).order_by(
        Task.id.desc()
    ).all()

    return render_template(
        "tasks.html",
        user=user,
        tasks=tasks_list
    )


# ============================================================
# COMPLETE TASK
# ============================================================

@app.route(
    "/tasks/<int:task_id>/complete"
)
def complete_task(task_id):

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first()

    if task:

        task.completed = True

        db.session.commit()

    return redirect(
        url_for("tasks")
    )


# ============================================================
# DELETE TASK
# ============================================================

@app.route(
    "/tasks/<int:task_id>/delete",
    methods=["GET", "POST"]
)
def delete_task(task_id):

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first()

    if task:

        db.session.delete(
            task
        )

        db.session.commit()

    return redirect(
        url_for("tasks")
    )


# ============================================================
# GOALS
# ============================================================

@app.route(
    "/goals",
    methods=["GET", "POST"]
)
def goals():

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        if title:

            goal = Goal(
                title=title,
                completed=False,
                user_id=user.id
            )

            db.session.add(
                goal
            )

            db.session.commit()

        return redirect(
            url_for("goals")
        )

    goals_list = Goal.query.filter_by(
        user_id=user.id
    ).order_by(
        Goal.id.desc()
    ).all()

    return render_template(
        "goals.html",
        user=user,
        goals=goals_list
    )


# ============================================================
# COMPLETE GOAL
# ============================================================

@app.route(
    "/goals/complete/<int:goal_id>"
)
def complete_goal(goal_id):

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    goal = Goal.query.filter_by(
        id=goal_id,
        user_id=user.id
    ).first()

    if goal:

        goal.completed = True

        db.session.commit()

    return redirect(
        url_for("goals")
    )


# ============================================================
# DELETE GOAL
# ============================================================

@app.route(
    "/goals/delete/<int:goal_id>",
    methods=["GET", "POST"]
)
def delete_goal(goal_id):

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    goal = Goal.query.filter_by(
        id=goal_id,
        user_id=user.id
    ).first()

    if goal:

        db.session.delete(
            goal
        )

        db.session.commit()

    return redirect(
        url_for("goals")
    )


# ============================================================
# CALENDAR
# ============================================================

@app.route(
    "/calendar",
    methods=["GET", "POST"]
)
def calendar():

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        category = request.form.get(
            "category",
            "General"
        ).strip()

        event_date = request.form.get(
            "event_date",
            ""
        ).strip()

        event_time = request.form.get(
            "event_time",
            ""
        ).strip()

        if not title:

            return redirect(
                url_for("calendar")
            )

        try:

            if event_date and event_time:

                event_datetime = datetime.strptime(
                    f"{event_date} {event_time}",
                    "%Y-%m-%d %H:%M"
                )

            elif event_date:

                event_datetime = datetime.strptime(
                    event_date,
                    "%Y-%m-%d"
                )

            else:

                event_datetime = datetime.now()

        except ValueError:

            event_datetime = datetime.now()

        event = CalendarEvent(
            title=title,
            description=description,
            location=location,
            category=category or "General",
            event_date=event_datetime,
            user_id=user.id
        )

        db.session.add(
            event
        )

        db.session.commit()

        return redirect(
            url_for("calendar")
        )

    events = CalendarEvent.query.filter_by(
        user_id=user.id
    ).order_by(
        CalendarEvent.event_date.asc()
    ).all()

    now = datetime.now()

    upcoming_events = [
        event
        for event in events
        if event.event_date >= now
    ]

    past_events = [
        event
        for event in events
        if event.event_date < now
    ]

    return render_template(
        "calendar.html",
        user=user,
        events=events,
        upcoming_events=upcoming_events,
        past_events=past_events
    )


# ============================================================
# DELETE CALENDAR EVENT
# ============================================================

@app.route(
    "/calendar/delete/<int:event_id>",
    methods=["GET", "POST"]
)
def delete_calendar_event(event_id):

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    event = CalendarEvent.query.filter_by(
        id=event_id,
        user_id=user.id
    ).first()

    if event:

        db.session.delete(
            event
        )

        db.session.commit()

    return redirect(
        url_for("calendar")
    )


# ============================================================
# LIFE MEMORY
# ============================================================

@app.route(
    "/memory",
    methods=["GET", "POST"]
)
def memory():

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        content = request.form.get(
            "content",
            ""
        ).strip()

        category = request.form.get(
            "category",
            "General"
        ).strip()

        if title and content:

            memory_item = Memory(
                title=title,
                content=content,
                category=category or "General",
                user_id=user.id
            )

            db.session.add(
                memory_item
            )

            db.session.commit()

        return redirect(
            url_for("memory")
        )

    memories = Memory.query.filter_by(
        user_id=user.id
    ).order_by(
        Memory.created_at.desc()
    ).all()

    return render_template(
        "memory.html",
        user=user,
        memories=memories
    )


# ============================================================
# DELETE MEMORY
# ============================================================

@app.route(
    "/memory/delete/<int:memory_id>",
    methods=["GET", "POST"]
)
def delete_memory(memory_id):

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    memory_item = Memory.query.filter_by(
        id=memory_id,
        user_id=user.id
    ).first()

    if memory_item:

        db.session.delete(
            memory_item
        )

        db.session.commit()

    return redirect(
        url_for("memory")
    )


# ============================================================
# FINANCE
# ============================================================

@app.route(
    "/finance",
    methods=["GET", "POST"]
)
def finance():

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    # --------------------------------------------------------
    # ADD TRANSACTION
    # --------------------------------------------------------

    if request.method == "POST":

        transaction_type = request.form.get(
            "type",
            ""
        ).strip().lower()

        amount_text = request.form.get(
            "amount",
            ""
        ).strip()

        category = request.form.get(
            "category",
            "General"
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        transaction_date_text = request.form.get(
            "transaction_date",
            ""
        ).strip()

        if transaction_type not in [
            "income",
            "expense"
        ]:

            transactions = Transaction.query.filter_by(
                user_id=user.id
            ).order_by(
                Transaction.id.desc()
            ).all()

            income = sum(
                float(t.amount)
                for t in transactions
                if t.type == "income"
                or t.transaction_type == "income"
            )

            expenses = sum(
                float(t.amount)
                for t in transactions
                if t.type == "expense"
                or t.transaction_type == "expense"
            )

            return render_template(
                "finance.html",
                user=user,
                transactions=transactions,
                income=income,
                expenses=expenses,
                balance=income - expenses,
                error="Transaction type must be income or expense."
            )

        # ----------------------------------------------------
        # AMOUNT
        # ----------------------------------------------------

        try:

            amount = float(
                amount_text
            )

        except (
            ValueError,
            TypeError
        ):

            transactions = Transaction.query.filter_by(
                user_id=user.id
            ).order_by(
                Transaction.id.desc()
            ).all()

            income = sum(
                float(t.amount)
                for t in transactions
                if t.type == "income"
                or t.transaction_type == "income"
            )

            expenses = sum(
                float(t.amount)
                for t in transactions
                if t.type == "expense"
                or t.transaction_type == "expense"
            )

            return render_template(
                "finance.html",
                user=user,
                transactions=transactions,
                income=income,
                expenses=expenses,
                balance=income - expenses,
                error="Please enter a valid amount."
            )

        if amount <= 0:

            return redirect(
                url_for("finance")
            )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        if transaction_date_text:

            try:

                transaction_datetime = datetime.strptime(
                    transaction_date_text,
                    "%Y-%m-%d"
                )

            except ValueError:

                transaction_datetime = datetime.now()

        else:

            transaction_datetime = datetime.now()

        # ----------------------------------------------------
        # CREATE TRANSACTION
        # ----------------------------------------------------

        transaction = Transaction(
            amount=amount,
            transaction_type=transaction_type,
            type=transaction_type,
            category=category or "General",
            description=description,
            transaction_date=transaction_datetime,
            user_id=user.id
        )

        db.session.add(
            transaction
        )

        db.session.commit()

        return redirect(
            url_for("finance")
        )

    # --------------------------------------------------------
    # GET FINANCE DATA
    # --------------------------------------------------------

    transactions = Transaction.query.filter_by(
        user_id=user.id
    ).order_by(
        Transaction.id.desc()
    ).all()

    income = sum(
        float(t.amount)
        for t in transactions
        if t.type == "income"
        or t.transaction_type == "income"
    )

    expenses = sum(
        float(t.amount)
        for t in transactions
        if t.type == "expense"
        or t.transaction_type == "expense"
    )

    balance = income - expenses

    return render_template(
        "finance.html",
        user=user,
        transactions=transactions,
        income=income,
        expenses=expenses,
        balance=balance
    )


# ============================================================
# DELETE TRANSACTION
# ============================================================

@app.route(
    "/finance/delete/<int:transaction_id>",
    methods=["GET", "POST"]
)
def delete_transaction(transaction_id):

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=user.id
    ).first()

    if transaction:

        db.session.delete(
            transaction
        )

        db.session.commit()

    return redirect(
        url_for("finance")
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route(
    "/settings",
    methods=["GET", "POST"]
)
def settings():

    user = get_current_user()

    if user is None:

        return redirect(
            url_for("login")
        )

    success = None
    error = None

    if request.method == "POST":

        action = request.form.get(
            "action",
            "profile"
        ).strip()

        # ----------------------------------------------------
        # PROFILE
        # ----------------------------------------------------

        if action == "profile":

            name = request.form.get(
                "name",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            if not name:

                error = "Name cannot be empty."

            elif not email:

                error = (
                    "Email address cannot be empty."
                )

            else:

                existing_user = User.query.filter(
                    User.email == email,
                    User.id != user.id
                ).first()

                if existing_user:

                    error = (
                        "That email address is already being used."
                    )

                else:

                    user.name = name
                    user.email = email

                    db.session.commit()

                    success = (
                        "Your profile has been updated successfully."
                    )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        elif action == "password":

            current_password = request.form.get(
                "current_password",
                ""
            )

            new_password = request.form.get(
                "new_password",
                ""
            )

            confirm_password = request.form.get(
                "confirm_password",
                ""
            )

            if not current_password:

                error = (
                    "Please enter your current password."
                )

            elif not check_password_hash(
                user.password,
                current_password
            ):

                error = (
                    "Current password is incorrect."
                )

            elif len(new_password) < 6:

                error = (
                    "New password must contain at least "
                    "6 characters."
                )

            elif new_password != confirm_password:

                error = (
                    "New passwords do not match."
                )

            else:

                user.password = generate_password_hash(
                    new_password
                )

                db.session.commit()

                success = (
                    "Your password has been changed successfully."
                )

        else:

            error = (
                "Invalid settings action."
            )

    return render_template(
        "settings.html",
        user=user,
        success=success,
        error=error
    )


# ============================================================
# AI ASSISTANT
# ============================================================

@app.route(
    "/ai",
    methods=["GET", "POST"]
)
def ai():

    user = login_required()

    if not user:

        return redirect(
            url_for("login")
        )

    response = None
    message = ""

    if request.method == "POST":

        message = request.form.get(
            "message",
            ""
        ).strip()

        lower_message = message.lower()

        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if not message:

            response = (
                "Please type a message first. 🤖"
            )

        # ----------------------------------------------------
        # HELLO
        # ----------------------------------------------------

        elif (
            "hello" in lower_message
            or "hi" in lower_message
            or "hey" in lower_message
        ):

            response = (
                f"Hello {user.name}! 👋\n\n"
                "I'm your LIFEOS Assistant. "
                "I can help you manage tasks, goals, "
                "memories and finances."
            )

        # ----------------------------------------------------
        # ADD TASK
        # ----------------------------------------------------

        elif (
            "add task" in lower_message
            or "create task" in lower_message
            or "new task" in lower_message
        ):

            task_title = ""

            if "add task" in lower_message:

                position = lower_message.find(
                    "add task"
                )

                task_title = message[
                    position + len("add task"):
                ].strip()

            elif "create task" in lower_message:

                position = lower_message.find(
                    "create task"
                )

                task_title = message[
                    position + len("create task"):
                ].strip()

            elif "new task" in lower_message:

                position = lower_message.find(
                    "new task"
                )

                task_title = message[
                    position + len("new task"):
                ].strip()

            task_title = task_title.strip(
                " :.-"
            )

            if task_title:

                task = Task(
                    title=task_title,
                    completed=False,
                    user_id=user.id
                )

                db.session.add(
                    task
                )

                db.session.commit()

                response = (
                    "Done! ✅\n\n"
                    "I added this task:\n\n"
                    f"📋 {task_title}"
                )

            else:

                response = (
                    "Sure! 📋\n\n"
                    "Try:\n"
                    "Add task Study Python"
                )

        # ----------------------------------------------------
        # ADD GOAL
        # ----------------------------------------------------

        elif (
            "add goal" in lower_message
            or "create goal" in lower_message
            or "new goal" in lower_message
        ):

            goal_title = ""

            if "add goal" in lower_message:

                position = lower_message.find(
                    "add goal"
                )

                goal_title = message[
                    position + len("add goal"):
                ].strip()

            elif "create goal" in lower_message:

                position = lower_message.find(
                    "create goal"
                )

                goal_title = message[
                    position + len("create goal"):
                ].strip()

            elif "new goal" in lower_message:

                position = lower_message.find(
                    "new goal"
                )

                goal_title = message[
                    position + len("new goal"):
                ].strip()

            goal_title = goal_title.strip(
                " :.-"
            )

            if goal_title:

                goal = Goal(
                    title=goal_title,
                    completed=False,
                    user_id=user.id
                )

                db.session.add(
                    goal
                )

                db.session.commit()

                response = (
                    "Done! 🎯\n\n"
                    "I added this goal:\n\n"
                    f"🎯 {goal_title}"
                )

            else:

                response = (
                    "Sure! 🎯\n\n"
                    "Try:\n"
                    "Add goal Learn Python"
                )

        # ----------------------------------------------------
        # FINANCE
        # ----------------------------------------------------

        elif (
            "balance" in lower_message
            or "money" in lower_message
            or "spent" in lower_message
            or "income" in lower_message
            or "expense" in lower_message
        ):

            transactions = Transaction.query.filter_by(
                user_id=user.id
            ).all()

            income = sum(
                float(t.amount)
                for t in transactions
                if t.type == "income"
                or t.transaction_type == "income"
            )

            expenses = sum(
                float(t.amount)
                for t in transactions
                if t.type == "expense"
                or t.transaction_type == "expense"
            )

            balance = income - expenses

            response = (
                "💰 Your LIFEOS Finance\n\n"
                f"Income: KSh {income:,.2f}\n"
                f"Expenses: KSh {expenses:,.2f}\n"
                f"Balance: KSh {balance:,.2f}"
            )

        # ----------------------------------------------------
        # TASKS
        # ----------------------------------------------------

        elif "task" in lower_message:

            task_count = Task.query.filter_by(
                user_id=user.id
            ).count()

            completed_tasks = Task.query.filter_by(
                user_id=user.id,
                completed=True
            ).count()

            pending_tasks = (
                task_count - completed_tasks
            )

            response = (
                "📋 Your LIFEOS Tasks\n\n"
                f"Total: {task_count}\n"
                f"Completed: {completed_tasks}\n"
                f"Pending: {pending_tasks}"
            )

        # ----------------------------------------------------
        # GOALS
        # ----------------------------------------------------

        elif "goal" in lower_message:

            goal_count = Goal.query.filter_by(
                user_id=user.id
            ).count()

            completed_goals = Goal.query.filter_by(
                user_id=user.id,
                completed=True
            ).count()

            pending_goals = (
                goal_count - completed_goals
            )

            response = (
                "🎯 Your LIFEOS Goals\n\n"
                f"Total: {goal_count}\n"
                f"Completed: {completed_goals}\n"
                f"Active: {pending_goals}"
            )

        # ----------------------------------------------------
        # PRODUCTIVITY
        # ----------------------------------------------------

        elif (
            "productivity" in lower_message
            or "productive" in lower_message
        ):

            response = (
                "🚀 Here's a simple productivity plan:\n\n"
                "1. Choose your most important task.\n"
                "2. Work without distractions.\n"
                "3. Complete smaller tasks afterward.\n"
                "4. Review your goals.\n"
                "5. Plan tomorrow."
            )

        # ----------------------------------------------------
        # HELP
        # ----------------------------------------------------

        elif "help" in lower_message:

            response = (
                "🤖 Here's what I can do:\n\n"
                "📋 Add tasks\n"
                "🎯 Add goals\n"
                "📊 Check tasks\n"
                "📊 Check goals\n"
                "💰 Check finances\n"
                "🚀 Give productivity advice\n\n"
                "Examples:\n"
                "• Add task Study Python\n"
                "• Add goal Learn AI\n"
                "• How many tasks do I have?\n"
                "• What's my balance?"
            )

        # ----------------------------------------------------
        # WHO ARE YOU
        # ----------------------------------------------------

        elif (
            "who are you" in lower_message
            or "what are you" in lower_message
        ):

            response = (
                "I'm LIFEOS Assistant 🤖.\n\n"
                "I'm your personal productivity "
                "assistant inside LIFEOS."
            )

        # ----------------------------------------------------
        # THANKS
        # ----------------------------------------------------

        elif (
            "thank" in lower_message
            or "thanks" in lower_message
        ):

            response = (
                "You're welcome! 😊\n\n"
                "Let's keep building LIFEOS."
            )

        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------

        else:

            response = (
                "I'm not sure how to handle that yet. 🤔\n\n"
                "Try asking about your tasks, goals "
                "or finances.\n\n"
                "Example:\n"
                "• Add task Study Python\n"
                "• Add goal Learn AI\n"
                "• What's my balance?\n"
                "• Help"
            )

    return render_template(
        "ai.html",
        user=user,
        message=message,
        response=response
    )


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <!DOCTYPE html>
    <html>

    <head>
        <title>LIFEOS - 404</title>

        <style>

            body {
                font-family: Arial;
                text-align: center;
                padding: 80px;
                background: #f5f7fb;
            }

            a {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 20px;
                background: #4f46e5;
                color: white;
                text-decoration: none;
                border-radius: 8px;
            }

        </style>

    </head>

    <body>

        <h1>404</h1>

        <h2>Page not found</h2>

        <p>
            The LIFEOS page you requested does not exist.
        </p>

        <a href="/">
            Return to Dashboard
        </a>

    </body>

    </html>
    """, 404


# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_error(error):

    db.session.rollback()

    return """
    <!DOCTYPE html>
    <html>

    <head>
        <title>LIFEOS - Error</title>

        <style>

            body {
                font-family: Arial;
                text-align: center;
                padding: 80px;
                background: #f5f7fb;
            }

            a {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 20px;
                background: #4f46e5;
                color: white;
                text-decoration: none;
                border-radius: 8px;
            }

        </style>

    </head>

    <body>

        <h1>Something went wrong</h1>

        <p>
            LIFEOS encountered an unexpected error.
        </p>

        <a href="/">
            Return to Dashboard
        </a>

    </body>

    </html>
    """, 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )