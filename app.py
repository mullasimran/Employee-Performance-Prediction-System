from flask import Flask, render_template, request,redirect,send_file,session
import joblib
import pandas as pd
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key="employee_performance_secret_key"

@app.route("/admin")
def admin():
    return render_template("admin.html")


# ---------------- DATABASE SETUP ----------------

def init_db():
    conn = sqlite3.connect("prediction_history.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT,
            department TEXT,
            job_title TEXT,
            location TEXT,
            experience INTEGER,
            status TEXT,
            work_mode TEXT,
            salary INTEGER,
            rating INTEGER,
            full_name TEXT,
            result TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- LOAD MODEL ----------------

model = joblib.load("model/model.pkl")
encoders = joblib.load("model/encoders.pkl")

print(encoders["Department"].classes_)
print(encoders["Job_Title"].classes_)
print(encoders["Location"].classes_)


# ---------------- HOME PAGE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["admin_logged_in"] = True

            return redirect("admin")

        else:

            return render_template(
                "login.html",
                error="Invalid username or password"
            )

    return render_template("login.html")
@app.route("/")
def home():
    if not session.get("admin_logged_in"):
        return redirect("/login")

    return render_template(
        "index.html",
        locations=encoders["Location"].classes_
    )


# ---------------- PREDICTION ----------------

@app.route("/predict", methods=["GET","POST"])
def predict():
    if request.method=="GET":
        return render_template("index.html",location=encoders["Location"].classes_)
    full_name=request.form["Full_Name"]

    data = {
        "Department": [
            int(request.form["Department"])
        ],

        "Job_Title": [
            encoders["Job_Title"].transform(
                [request.form["Job_Title"]]
            )[0]
        ],

        "Location": [
            encoders["Location"].transform(
                [request.form["Location"]]
            )[0]
        ],

        "Experience_Years": [
            int(request.form["Experience_Years"])
        ],

        "Status": [
            int(request.form["Status"])
        ],

        "Work_Mode": [
            int(request.form["Work_Mode"])
        ],

        "Salary_INR": [
            int(request.form["Salary_INR"])
        ]
    }


    # Create DataFrame
    df = pd.DataFrame(data)


    # Make prediction
    prediction = model.predict(df)

    rating = int(prediction[0])


    # Convert rating to performance level
    if rating == 1:
        result = "Poor"

    elif rating == 2:
        result = "Below Average"

    elif rating == 3:
        result = "Average"

    elif rating == 4:
        result = "Good"

    else:
        result = "Excellent"

        
   # Performance Recommendation

    if rating == 1:
        recommendation = "Performance improvement is required. Training and regular feedback are recommended."

    elif rating == 2:
        recommendation = "Performance is below expectations. Skill development and guidance are recommended."

    elif rating == 3:
        recommendation = "Performance is average. Regular feedback and further skill development are recommended."

    elif rating == 4:
        recommendation = "Good performance. Continue the current work and focus on further improvement."

    else:
        recommendation = "Excellent performance. Employee can be considered for recognition and additional responsibilities."


    # ---------------- READABLE VALUES ----------------

    department_map = {
        "0": "Finance",
        "1": "HR",
        "2": "IT",
        "3": "Marketing",
        "4": "Operations",
        "5": "R&D",
        "6": "Sales"
    }


    status_map = {
        "0": "Inactive",
        "1": "Active"
    }


    work_mode_map = {
        "0": "Work From Office",
        "1": "Hybrid",
        "2": "Remote"
    }


    department_name = department_map.get(
        request.form["Department"],
        request.form["Department"]
    )


    status_name = status_map.get(
        request.form["Status"],
        request.form["Status"]
    )


    work_mode_name = work_mode_map.get(
        request.form["Work_Mode"],
        request.form["Work_Mode"]
    )


    # ---------------- SAVE TO DATABASE ----------------

    conn = sqlite3.connect("prediction_history.db")

    conn.execute("""
        INSERT INTO predictions
        (
            date_time,
            department,
            job_title,
            location,
            experience,
            status,
            work_mode,
            salary,
            rating,
            full_name,
            result
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    """, (
        datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        department_name,
        request.form["Job_Title"],
        request.form["Location"],
        int(request.form["Experience_Years"]),
        status_name,
        work_mode_name,
        int(request.form["Salary_INR"]),
        rating,
        full_name,
        result
    ))


    conn.commit()
    conn.close()


    # ---------------- RESULT PAGE ----------------

    return render_template(
        "result.html",
        rating=rating,
        full_name=full_name,
        result=result,
        recommendation=recommendation,
        department=department_name,
        job_title=request.form["Job_Title"],
        location=request.form["Location"],
        experience=request.form["Experience_Years"],
        status=status_name,
        work_mode=work_mode_name,
        salary=request.form["Salary_INR"]
    )


# ---------------- HISTORY PAGE ----------------
@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect("/login")

@app.route("/history")
def history():

    conn = sqlite3.connect("prediction_history.db")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM predictions
        ORDER BY id DESC
    """)

    history_data = cursor.fetchall()

    conn.close()


    return render_template(
        "history.html",
        history=history_data
    )

@app.route("/reports")
def reports():

    conn = sqlite3.connect("prediction_history.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM predictions ORDER BY id DESC")

    reports_data = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 5")
    excellent = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 4")
    good = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 3")
    average = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "reports.html",
        reports=reports_data,
        total=total,
        excellent=excellent,
        good=good,
        average=average
    )

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("prediction_history.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 5")
    excellent = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 4")
    good = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 3")
    average = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 2")
    below_average = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rating = 1")
    poor = cursor.fetchone()[0]

    conn.close()

    if total > 0:
        excellent_percent = round((excellent / total) * 100)
        good_percent = round((good / total) * 100)
        average_percent = round((average / total) * 100)
        below_average_percent = round((below_average / total) * 100)
        poor_percent = round((poor / total) * 100)
    else:
        excellent_percent = 0
        good_percent = 0
        average_percent = 0
        below_average_percent = 0
        poor_percent = 0

    return render_template(
        "dashboard.html",
        total=total,
        excellent=excellent,
        good=good,
        average=average,
        below_average=below_average,
        poor=poor,
        excellent_percent=excellent_percent,
        good_percent=good_percent,
        average_percent=average_percent,
        below_average_percent=below_average_percent,
        poor_percent=poor_percent
    )
@app.route("/delete/<int:prediction_id>")
def delete_prediction(prediction_id):

    conn = sqlite3.connect("prediction_history.db")

    conn.execute(
        "DELETE FROM predictions WHERE id = ?",
        (prediction_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/history")

@app.route("/download")
def download_history():

    conn = sqlite3.connect("prediction_history.db")

    df = pd.read_sql_query(
        "SELECT * FROM predictions ORDER BY id DESC",
        conn
    )

    conn.close()

    file_name = "prediction_history.csv"

    df.to_csv(file_name, index=False)

    return send_file(
        file_name,
        as_attachment=True,
        download_name="prediction_history.csv"
    )



# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)