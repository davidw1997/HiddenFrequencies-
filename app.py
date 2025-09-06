from flask import Flask, render_template, request, redirect, flash, session, url_for
from datetime import date
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "dpg-d2th67vdiees7388k8l0-a"),  # Render internal hostname
        database=os.environ.get("DB_NAME", "hidden_frequenciesdb"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "your-password-here"),  # Replace with Render secret
        port=os.environ.get("DB_PORT", "5432")
    )
    return conn

# -------------------- Routes --------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/videos")
def videos():
    return render_template("videos.html")

@app.route("/blog")
def blog():
    return render_template("blog.html")

@app.route("/book")
def book():
    return render_template("book.html")

@app.route("/submit", methods=["POST"])
def submit():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        today = date.today()

        if not name or not email:
            flash("Please fill in all fields", "error")
            return redirect(url_for("index"))

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO subscribers (name, email, signup_date) VALUES (%s, %s, %s)",
                (name, email, today)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash("Subscription successful!", "success")
        except Exception as e:
            flash(f"Database error: {str(e)}", "error")

        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7700)))
