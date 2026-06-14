from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import pandas as pd

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add")
def add():
    return render_template("add.html")


@app.route("/add_expense", methods=["POST"])
def add_expense():
    amount = request.form["amount"]
    category = request.form["category"]
    if category == "Other":
        category = request.form["custom_category"].title()
    date = request.form["date"]
    description = request.form["description"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO expenses (amount, category, date, description)
        VALUES (?, ?, ?, ?)
    """, (amount, category, date, description))
    conn.commit()
    conn.close()

    return render_template("success.html")


@app.route("/view")
def view():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    search = request.args.get("search")
    if search:
        cur.execute("""
            SELECT * FROM expenses
            WHERE category LIKE ? OR description LIKE ?
        """, (f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM expenses")

    data = cur.fetchall()
    conn.close()

    return render_template("view.html", data=data)


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/view")


@app.route("/summary")
def summary():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    selected_year = request.args.get("year")
    selected_month = request.args.get("month")
    years = sorted(df["date"].dt.year.unique())

    if selected_year:
        df = df[df["date"].dt.year == int(selected_year)]
    if selected_month:
        df = df[df["date"].dt.month == int(selected_month)]

    if df.empty:
        total_expense = 0
        average_transaction = 0
        highest_category = "No Data"
        chart_labels = []
        chart_values = []
    else:
        total_expense = round(df["amount"].sum(), 2)
        highest_category = df.groupby("category")["amount"].sum().idxmax()
        average_transaction = round(df["amount"].mean(), 2)

        df["category"] = df["category"].str.title()
        category_data = df.groupby("category")["amount"].sum()
        chart_labels = category_data.index.tolist()
        chart_values = category_data.values.tolist()

    return render_template(
        "summary.html",
        total_expense=total_expense,
        average_transaction=average_transaction,
        category=highest_category,
        years=years,
        selected_year=selected_year,
        selected_month=selected_month,
        no_data=df.empty,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@app.route("/calendar")
def calendar():
    return render_template("calendar.html")


@app.route("/api/expenses")
def api_expenses():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT id, amount, category, date, description FROM expenses")
    rows = cur.fetchall()
    conn.close()

    expenses = []
    for r in rows:
        expenses.append({
            "id": r[0],
            "amount": r[1],
            "category": r[2],
            "date": r[3],
            "description": r[4]
        })
    return jsonify(expenses)


if __name__ == "__main__":
    app.run(debug=True)