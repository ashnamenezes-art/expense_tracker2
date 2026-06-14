from flask import Flask, render_template,request,redirect
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
        INSERT INTO expenses
        (amount, category, date, description)
        VALUES (?, ?, ?, ?)
    """, (amount, category, date, description))

    conn.commit()
    conn.close()
    return """
<!DOCTYPE html>
<html>
<head>
<style>

body{
    background:#f4f6f9;
    font-family:Arial,sans-serif;
    text-align:center;
}

.success-card{
    background:white;
    width:500px;
    margin:100px auto;
    padding:40px;
    border-radius:12px;
    box-shadow:0 4px 15px rgba(0,0,0,0.1);
}

.success-icon{
    font-size:60px;
    color:green;
}

h2{
    color:#2c3e50;
}

button{
    background:#3498db;
    color:white;
    border:none;
    padding:10px 20px;
    border-radius:6px;
    cursor:pointer;
    margin:5px;
}

button:hover{
    background:#2980b9;
}

</style>
</head>

<body>

<div class="success-card">

    <h2>Expense Added Successfully!</h2>

    <p>Your expense has been saved to the database.</p>

    <br>

    <a href='/'>
        <button> Back to Dashboard</button>
    </a>

    <a href='/add'>
        <button> Add Another Expense</button>
    </a>

</div>

</body>
</html>
"""

@app.route("/view")
def view():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    search = request.args.get("search")

    if search:
     cur.execute("""
        SELECT * FROM expenses
        WHERE category LIKE ?
        OR description LIKE ?
    """, (f"%{search}%", f"%{search}%"))
    else:
      cur.execute("SELECT * FROM expenses")
 
    data = cur.fetchall()

    conn.close()

    return render_template("view.html", data=data)

@app.route("/delete/<int:id>")
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
    df["date"] = pd.to_datetime(df["date"])
    today = pd.Timestamp.today()
    year_name = today.year
    month_name = today.strftime("%B %Y")
    week_name = f"Week {today.isocalendar().week} ({today.year})"
    week_data = df[
    (df["date"].dt.isocalendar().week == today.isocalendar().week) &
    (df["date"].dt.year == today.year)
     ]

    week_total = week_data["amount"].sum()
    month_data = df[
    (df["date"].dt.month == today.month) &
    (df["date"].dt.year == today.year)
     ]

    month_total = month_data["amount"].sum()

# Current year
    year_data = df[
    df["date"].dt.year == today.year
     ]
    year_total = year_data["amount"].sum()
    
    
    
    conn.close()

    if df.empty:
        return "No expense data available."

    total_expense = np.sum(df["amount"])
    average_transaction = round(df["amount"].mean(), 2)

    highest_category = (
        df.groupby("category")["amount"]
        .sum()
        .idxmax()
    )

    # Generate chart
    df["category"] = df["category"].str.title()
    category_data = df.groupby("category")["amount"].sum()

    plt.figure(figsize=(6,6))
    plt.pie(
        category_data,
        labels=category_data.index,
        autopct='%1.1f%%'
    )

    plt.title("Expense Distribution")
    plt.savefig("static/chart.png")
    plt.close()

    return render_template(
    "summary.html",
    year_total=year_total,
    month_total=month_total,
    week_total=week_total,
    year_name=year_name,
    month_name=month_name,
    week_name=week_name,
    category=highest_category
)
    
if __name__ == "__main__":
    app.run(debug=True)