import math
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models import db
from models.goal import Goal
from models.target import Target
from models.transaction import Transaction
from models.user import User

bp = Blueprint("api", __name__, url_prefix="/api")

EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Education",
    "Entertainment",
    "Bills",
    "Shopping",
    "Health",
    "Other",
]
PAYMENT_METHODS = [
    "Cash",
    "Card",
    "Bank Transfer",
    "Google Pay",
    "PhonePe",
    "Paytm",
    "BHIM UPI",
    "Other",
]


def month_bounds():
    today = datetime.utcnow().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        next_first = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_first = today.replace(month=today.month + 1, day=1)
    return first_day, next_first - timedelta(days=1)


def calculate_dashboard_metrics(user):
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")
    savings = income - expenses
    savings_rate = (savings / income * 100) if income > 0 else 0.0
    health_score = calculate_health_score(user)
    safe_to_spend = calculate_safe_to_spend(user)
    remaining_budget = income - expenses
    status = "Needs Attention"
    if health_score >= 80:
        status = "Excellent"
    elif health_score >= 65:
        status = "Good"
    elif health_score >= 50:
        status = "Fair"

    return {
        "total_income": round(income, 2),
        "total_expenses": round(expenses, 2),
        "total_savings": round(savings, 2),
        "savings_rate": round(savings_rate, 2),
        "remaining_budget": round(remaining_budget, 2),
        "health_score": health_score,
        "status": status,
        "safe_to_spend": round(safe_to_spend, 2),
        "transactions_count": len(transactions),
    }


def calculate_health_score(user):
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")
    if income <= 0:
        return 0

    savings_rate = (income - expenses) / income
    expense_ratio = expenses / income if income > 0 else 0
    goal_completion = 0
    goals = Goal.query.filter_by(user_id=user.id).all()
    if goals:
        completed = [g for g in goals if g.saved >= g.amount]
        goal_completion = len(completed) / len(goals) * 100

    consistent = 0
    if len(transactions) >= 5:
        consistent = min(len(transactions) / 30 * 100, 100)

    score = (max(savings_rate, 0) * 40) + ((1 - min(expense_ratio, 1.5)) * 20) + (goal_completion * 0.2) + (consistent * 0.2)
    score = max(0, min(100, round(score)))
    return score


def calculate_safe_to_spend(user):
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")
    remaining_budget = income - expenses
    today = datetime.utcnow().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    last_day = next_month - timedelta(days=1)
    days_left = max((last_day - today).days + 1, 1)
    return remaining_budget / days_left if days_left > 0 else 0


def get_coach_message(user):
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    if not transactions:
        return "Start recording your income and expenses so SmartLife can understand your financial habits."

    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")
    if expenses > income:
        return "Your expenses are higher than your current income. Consider reducing non-essential spending."

    food_spend = sum(t.amount for t in transactions if t.type == "expense" and t.category == "Food")
    target = Target.query.filter_by(user_id=user.id).first()
    if target and food_spend > target.food_target:
        return f"You have exceeded your food budget by ₹{round(food_spend - target.food_target, 2)}. Consider reducing unnecessary food purchases."

    savings_rate = (income - expenses) / income if income > 0 else 0
    if savings_rate >= 0.25:
        return "Great work! You are maintaining a strong savings rate."

    goals = Goal.query.filter_by(user_id=user.id).all()
    if goals:
        for goal in goals:
            if goal.amount > 0:
                percentage = (goal.saved / goal.amount) * 100
                if 60 <= percentage < 100:
                    return f"You're {round(percentage, 0)}% toward your {goal.name} goal. Keep contributing regularly."

    return "You are making steady progress. Keep tracking your spending to improve your financial habits."


def build_analytics(user):
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.asc()).all()
    income_total = sum(t.amount for t in transactions if t.type == "income")
    expense_total = sum(t.amount for t in transactions if t.type == "expense")

    income_vs_expense = {
        "labels": ["Income", "Expenses"],
        "values": [round(income_total, 2), round(expense_total, 2)],
    }

    category_totals = {}
    for t in transactions:
        if t.type == "expense":
            category_totals[t.category] = category_totals.get(t.category, 0) + t.amount
    expense_category = {
        "labels": list(category_totals.keys()),
        "values": [round(v, 2) for v in category_totals.values()],
    }

    monthly = {}
    for t in transactions:
        key = t.date.strftime("%b %Y") if t.date else "Unknown"
        monthly[key] = monthly.get(key, {"income": 0, "expense": 0})
        if t.type == "income":
            monthly[key]["income"] += t.amount
        else:
            monthly[key]["expense"] += t.amount
    monthly_labels = list(monthly.keys())
    monthly_income = [round(monthly[k]["income"], 2) for k in monthly_labels]
    monthly_expense = [round(monthly[k]["expense"], 2) for k in monthly_labels]

    savings_trend = []
    current = 0
    for entry in sorted(monthly.items(), key=lambda item: item[0]):
        monthly_income_value = entry[1]["income"]
        monthly_expense_value = entry[1]["expense"]
        current += monthly_income_value - monthly_expense_value
        savings_trend.append(round(current, 2))

    return {
        "income_vs_expense": income_vs_expense,
        "expense_category": expense_category,
        "monthly": {"labels": monthly_labels, "income": monthly_income, "expense": monthly_expense},
        "savings_trend": {"labels": monthly_labels or ["No data"], "values": savings_trend or [0]},
    }


def build_upi_stats(user):
    stats = {"Google Pay": 0, "PhonePe": 0, "Paytm": 0, "BHIM UPI": 0}
    for transaction in Transaction.query.filter_by(user_id=user.id).all():
        if transaction.payment in stats:
            stats[transaction.payment] += 1
    return stats


def build_literacy_lessons():
    return [
        {
            "topic": "What is budgeting?",
            "explanation": "A budget is a plan for how your money should be used across income, needs, savings, and goals.",
            "example": "If you earn ₹30,000 and spend ₹18,000, you can assign ₹6,000 to savings and ₹6,000 to goals or buffer.",
            "tip": "Budget on a monthly basis and review it every week.",
        },
        {
            "topic": "What is saving?",
            "explanation": "Saving means setting aside money now for future needs, emergencies, or planned purchases.",
            "example": "Saving ₹2,000 every month can accumulate to a significant amount over a year.",
            "tip": "Automate a transfer on payday to make saving consistent.",
        },
        {
            "topic": "What is an emergency fund?",
            "explanation": "An emergency fund is cash set aside to handle unexpected costs without relying on debt.",
            "example": "A basic emergency fund could cover 3 to 6 months of essential expenses.",
            "tip": "Keep it in a separate, easily accessible account.",
        },
        {
            "topic": "Needs vs wants",
            "explanation": "Needs are essential expenses; wants are nice-to-have purchases that can be reduced when necessary.",
            "example": "Rent and groceries are needs, while impulse shopping or entertainment subscriptions are often wants.",
            "tip": "Pause non-essential purchases for 24 hours before buying them.",
        },
        {
            "topic": "How to control unnecessary spending",
            "explanation": "Track spending categories and identify patterns that drain cash without adding much value.",
            "example": "Cancelling one unused subscription or reducing eating out can free a meaningful amount each month.",
            "tip": "Use a spending cap for each discretionary category.",
        },
        {
            "topic": "What is compound interest?",
            "explanation": "Compound interest means earning interest on both the principal and the interest already earned.",
            "example": "Investing early allows small regular contributions to grow significantly over time.",
            "tip": "Start early; time is one of the strongest advantages in investing.",
        },
        {
            "topic": "How to use UPI safely",
            "explanation": "UPI is convenient but users should verify beneficiaries, use trusted apps, and avoid sharing PINs or OTPs.",
            "example": "Always confirm the recipient name before sending money for a purchase or bill payment.",
            "tip": "Only use official payment apps and avoid clicking suspicious links.",
        },
        {
            "topic": "Basic investing concepts",
            "explanation": "Investing means putting money into assets with the goal of long-term growth, with risk varying by asset type.",
            "example": "A diversified portfolio can reduce concentration risk compared with investing all money into one asset.",
            "tip": "Learn the basics before investing heavily; avoid chasing short-term hype.",
        },
        {
            "topic": "Credit score basics",
            "explanation": "A credit score reflects how reliably someone manages debt and repayments over time.",
            "example": "Paying credit card balances on time and keeping utilization manageable can help protect a score.",
            "tip": "Track due dates and avoid unnecessary borrowing.",
        },
        {
            "topic": "Debt management basics",
            "explanation": "Good debt management means prioritizing repayments and avoiding interest-heavy borrowing for avoidable expenses.",
            "example": "A high-interest credit card balance can be more expensive than a lower-interest personal loan.",
            "tip": "Pay high-interest debt first when possible.",
        },
        {
            "topic": "Personal financial planning",
            "explanation": "Financial planning connects income, spending, saving, and future goals into one consistent strategy.",
            "example": "Planning for a trip, a laptop, and emergency savings at the same time creates a realistic monthly roadmap.",
            "tip": "Combine short-term and long-term goals into one plan with clear monthly target amounts.",
        },
    ]


def get_smart_insights(user):
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    if not transactions:
        return []
    category_totals = {}
    for t in transactions:
        if t.type == "expense":
            category_totals[t.category] = category_totals.get(t.category, 0) + t.amount
    highest_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else "No data"
    income = sum(t.amount for t in transactions if t.type == "income")
    expense = sum(t.amount for t in transactions if t.type == "expense")
    savings_rate = ((income - expense) / income * 100) if income > 0 else 0
    payment_counts = {}
    for t in transactions:
        payment_counts[t.payment] = payment_counts.get(t.payment, 0) + 1
    most_used = max(payment_counts.items(), key=lambda x: x[1])[0] if payment_counts else "No data"
    insights = [
        f"{highest_category} is your highest expense category this month.",
        f"You have saved {round(savings_rate, 2)}% of your recorded income.",
        f"You made {len(transactions)} transactions this month.",
        f"Your budget utilization is {round((expense / income) * 100, 2) if income > 0 else 0}%.",
        f"Most-used payment method: {most_used}.",
    ]
    return insights


@bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    target = Target.query.filter_by(user_id=current_user.id).first()
    food_spend = sum(t.amount for t in transactions if t.type == "expense" and t.category == "Food")
    response = {
        "user": user.to_public_dict(),
        "metrics": calculate_dashboard_metrics(user),
        "coach": get_coach_message(user),
        "analytics": build_analytics(user),
        "upi": build_upi_stats(user),
        "insights": get_smart_insights(user),
        "lessons": build_literacy_lessons(),
        "transactions": [t.to_dict() for t in transactions],
        "goals": [g.to_dict() for g in goals],
        "targets": target.to_dict() if target else {
            "income_target": 0,
            "expense_target": 0,
            "savings_target": 0,
            "food_target": 0,
        },
        "food_spend": round(food_spend, 2),
    }
    return jsonify(response)


@bp.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    if request.method == "GET":
        query = Transaction.query.filter_by(user_id=current_user.id)
        transaction_type = request.args.get("type")
        category = request.args.get("category")
        payment = request.args.get("payment")
        search = request.args.get("search", "")

        if transaction_type:
            query = query.filter_by(type=transaction_type)
        if category:
            query = query.filter_by(category=category)
        if payment:
            query = query.filter_by(payment=payment)
        if search:
            q = "%{}%".format(search)
            query = query.filter((Transaction.note.ilike(q)) | (Transaction.category.ilike(q)) | (Transaction.payment.ilike(q)))
        data = [t.to_dict() for t in query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()]
        return jsonify({"transactions": data})

    data = request.get_json(silent=True) or {}
    transaction_type = (data.get("type") or "").strip().lower()
    amount = data.get("amount")
    category = (data.get("category") or "").strip()
    payment = (data.get("payment") or "").strip()
    date_value = (data.get("date") or "").strip()
    note = (data.get("note") or "").strip()

    if transaction_type not in {"income", "expense"}:
        return jsonify({"success": False, "message": "Transaction type must be income or expense."}), 400
    if amount is None or float(amount) <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
    if category not in EXPENSE_CATEGORIES and transaction_type == "expense":
        return jsonify({"success": False, "message": "Please select a valid expense category."}), 400
    if payment not in PAYMENT_METHODS:
        return jsonify({"success": False, "message": "Please select a valid payment method."}), 400
    if not date_value:
        return jsonify({"success": False, "message": "Transaction date is required."}), 400

    try:
        parsed_date = datetime.fromisoformat(date_value).date()
    except ValueError:
        return jsonify({"success": False, "message": "Please enter a valid date."}), 400

    transaction = Transaction(
        user_id=current_user.id,
        type=transaction_type,
        amount=float(amount),
        category=category if category else "Other",
        payment=payment,
        date=parsed_date,
        note=note,
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({"success": True, "message": "Transaction added successfully.", "transaction": transaction.to_dict()})


@bp.route("/transactions/<int:transaction_id>", methods=["PUT", "DELETE"])
@login_required
def transaction_detail(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()
    if not transaction:
        return jsonify({"success": False, "message": "Transaction not found."}), 404

    if request.method == "DELETE":
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({"success": True, "message": "Transaction deleted."})

    data = request.get_json(silent=True) or {}
    transaction.type = (data.get("type") or transaction.type).lower()
    transaction.amount = float(data.get("amount") or transaction.amount)
    transaction.category = (data.get("category") or transaction.category).strip()
    transaction.payment = (data.get("payment") or transaction.payment).strip()
    if transaction.type not in {"income", "expense"}:
        return jsonify({"success": False, "message": "Transaction type must be income or expense."}), 400
    if transaction.amount <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
    if transaction.category not in EXPENSE_CATEGORIES and transaction.type == "expense":
        return jsonify({"success": False, "message": "Please select a valid expense category."}), 400
    if transaction.payment not in PAYMENT_METHODS:
        return jsonify({"success": False, "message": "Please select a valid payment method."}), 400
    try:
        if data.get("date"):
            transaction.date = datetime.fromisoformat(data["date"]).date()
    except ValueError:
        return jsonify({"success": False, "message": "Please enter a valid date."}), 400
    transaction.note = (data.get("note") or transaction.note or "").strip()
    db.session.commit()
    return jsonify({"success": True, "message": "Transaction updated."})


@bp.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    if request.method == "GET":
        return jsonify({"goals": [g.to_dict() for g in Goal.query.filter_by(user_id=current_user.id).all()]})

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    amount = float(data.get("amount") or 0)
    saved = float(data.get("saved") or 0)
    target_date = (data.get("target_date") or "").strip()

    if not name or amount <= 0:
        return jsonify({"success": False, "message": "Goal name and target amount are required."}), 400
    if saved < 0 or saved > amount:
        return jsonify({"success": False, "message": "Saved amount cannot be negative or exceed target."}), 400
    if not target_date:
        return jsonify({"success": False, "message": "Target date is required."}), 400
    try:
        parsed_date = datetime.fromisoformat(target_date).date()
    except ValueError:
        return jsonify({"success": False, "message": "Please enter a valid target date."}), 400

    goal = Goal(user_id=current_user.id, name=name, amount=amount, saved=saved, target_date=parsed_date)
    db.session.add(goal)
    db.session.commit()
    return jsonify({"success": True, "message": "Goal created successfully.", "goal": goal.to_dict()})


@bp.route("/goals/<int:goal_id>", methods=["PUT", "DELETE"])
@login_required
def goal_detail(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({"success": False, "message": "Goal not found."}), 404

    if request.method == "DELETE":
        db.session.delete(goal)
        db.session.commit()
        return jsonify({"success": True, "message": "Goal deleted."})

    data = request.get_json(silent=True) or {}
    goal.name = (data.get("name") or goal.name).strip()
    goal.amount = float(data.get("amount") or goal.amount)
    goal.saved = float(data.get("saved") or goal.saved)
    goal.target_date = datetime.fromisoformat(data["target_date"]).date() if data.get("target_date") else goal.target_date
    if not goal.name or goal.amount <= 0:
        return jsonify({"success": False, "message": "Goal name and target amount are required."}), 400
    if goal.saved < 0 or goal.saved > goal.amount:
        return jsonify({"success": False, "message": "Saved amount cannot be negative or exceed target."}), 400
    db.session.commit()
    return jsonify({"success": True, "message": "Goal updated successfully."})


@bp.route("/targets", methods=["GET", "PUT"])
@login_required
def targets():
    target = Target.query.filter_by(user_id=current_user.id).first()
    if request.method == "GET":
        return jsonify({"target": target.to_dict() if target else {
            "income_target": 0,
            "expense_target": 0,
            "savings_target": 0,
            "food_target": 0,
        }})

    data = request.get_json(silent=True) or {}
    if not target:
        target = Target(user_id=current_user.id)
        db.session.add(target)

    target.income_target = float(data.get("income_target") or target.income_target)
    target.expense_target = float(data.get("expense_target") or target.expense_target)
    target.savings_target = float(data.get("savings_target") or target.savings_target)
    target.food_target = float(data.get("food_target") or target.food_target)

    for field in ["income_target", "expense_target", "savings_target", "food_target"]:
        val = getattr(target, field)
        if val < 0:
            return jsonify({"success": False, "message": "Targets cannot be negative."}), 400

    target.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "message": "Financial target updated.", "target": target.to_dict()})


@bp.route("/profile", methods=["GET", "PUT"])
@login_required
def profile():
    if request.method == "GET":
        return jsonify({"user": current_user.to_public_dict()})

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    user_type = (data.get("user_type") or current_user.user_type).strip()
    bio = (data.get("bio") or current_user.bio or "").strip()

    if not name or not email:
        return jsonify({"success": False, "message": "Name and email are required."}), 400
    if "@" not in email or "." not in email:
        return jsonify({"success": False, "message": "Please provide a valid email address."}), 400

    existing = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing:
        return jsonify({"success": False, "message": "This email is already registered to another account."}), 409

    current_user.name = name
    current_user.email = email
    current_user.user_type = user_type or current_user.user_type
    current_user.bio = bio
    db.session.commit()
    return jsonify({"success": True, "message": "Profile updated successfully.", "user": current_user.to_public_dict()})


@bp.route("/logout", methods=["POST"])
@login_required
def logout_api():
    from flask_login import logout_user
    logout_user()
    return jsonify({"success": True, "message": "Logged out successfully."})


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})
