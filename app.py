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
    selected_year = request.args.get("year")
    selected_month = request.args.get("month")
    years = sorted(df["date"].dt.year.unique())
    if selected_year:
      df = df[df["date"].dt.year == int(selected_year)]

    if selected_month:
     df = df[df["date"].dt.month == int(selected_month)]
     
    
    conn.close()

    if df.empty:
        total_expense = 0
        average_transaction = 0
        highest_category = "No Data"
          
    total_expense = round(df["amount"].sum(), 2)
    if not df.empty:
     highest_category = (
        df.groupby("category")["amount"]
        .sum()
        .idxmax()
    )
    else:
     highest_category = "No Data"
    
    average_transaction = (
    round(df["amount"].mean(), 2)
    if not df.empty
    else 0
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
    total_expense=total_expense,
    average_transaction=average_transaction,
    category=highest_category,
    years=years,
    selected_year=selected_year,
    selected_month=selected_month,
    no_data=False if not df.empty else True
)
    
if __name__ == "__main__":
    app.run(debug=True)