from flask import Flask, render_template, request, redirect, flash, session, url_for
from datetime import date
import pymysql
import os

# Use PyMySQL for Termux compatibility
pymysql.install_as_MySQLdb()
import MySQLdb

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Connect to MariaDB using environment variables for Render deployment
db = MySQLdb.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    passwd=os.environ.get("DB_PASSWORD", ""),
    db=os.environ.get("DB_NAME", "hidden_frequencies")
)

# -------------------- Daily Quotes --------------------
quotes = [
    "The only limit is your mind.",
    "Happiness is a journey, not a destination.",
    "Every frequency has its hidden power.",
    "Change your thoughts, change your world.",
    "Small daily improvements lead to stunning results.",
    "Believe in yourself and all that you are.",
    "Energy flows where attention goes.",
    "Your vibe attracts your tribe."
]

def get_daily_quote():
    index = date.today().toordinal() % len(quotes)
    return quotes[index]

# -------------------- Public Routes --------------------
@app.route("/")
def home():
    daily_quote = get_daily_quote()
    return render_template("index.html", quote=daily_quote)

@app.route("/blog")
def blog():
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    cursor.close()
    daily_quote = get_daily_quote()
    return render_template("blog.html", quote=daily_quote, posts=posts)

@app.route("/subscribe", methods=["POST"])
def subscribe():
    name = request.form.get("name")
    email = request.form.get("email")
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO subscribers (name, email) VALUES (%s, %s)", (name, email))
        db.commit()
        flash("Thank you for subscribing!")
    except Exception as e:
        db.rollback()
        flash(f"Error: {e}")
    cursor.close()
    return redirect("/")

# -------------------- Admin Login/Logout --------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "password123":
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        else:
            flash("Invalid credentials")
            return redirect("/admin/login")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out")
    return redirect("/admin/login")

# -------------------- Admin Authentication --------------------
def admin_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Login required")
            return redirect("/admin/login")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# -------------------- Admin Dashboard --------------------
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM subscribers ORDER BY subscribed_at DESC")
    subscribers = cursor.fetchall()
    cursor.close()
    return render_template("admin_dashboard.html", subscribers=subscribers)

# -------------------- Blog Post Management --------------------
@app.route("/admin/posts")
@admin_required
def admin_posts():
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    cursor.close()
    return render_template("admin_posts.html", posts=posts)

@app.route("/admin/posts/add", methods=["GET", "POST"])
@admin_required
def add_post():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        cursor = db.cursor()
        cursor.execute("INSERT INTO posts (title, content) VALUES (%s, %s)", (title, content))
        db.commit()
        cursor.close()
        flash("Post added successfully!")
        return redirect("/admin/posts")
    return render_template("admin_add_post.html")

@app.route("/admin/posts/edit/<int:post_id>", methods=["GET", "POST"])
@admin_required
def edit_post(post_id):
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        cursor.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s", (title, content, post_id))
        db.commit()
        cursor.close()
        flash("Post updated successfully!")
        return redirect("/admin/posts")
    cursor.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
    post = cursor.fetchone()
    cursor.close()
    return render_template("admin_edit_post.html", post=post)

@app.route("/admin/posts/delete/<int:post_id>")
@admin_required
def delete_post(post_id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM posts WHERE id=%s", (post_id,))
    db.commit()
    cursor.close()
    flash("Post deleted successfully!")
    return redirect("/admin/posts")

# -------------------- Send Email to Subscribers (simulation) --------------------
@app.route("/admin/send_email", methods=["POST"])
@admin_required
def send_email():
    subject = request.form.get("subject")
    message = request.form.get("message")
    cursor = db.cursor()
    cursor.execute("SELECT email FROM subscribers")
    emails = [row[0] for row in cursor.fetchall()]
    cursor.close()
    # Implement actual email sending with SMTP or email service
    flash(f"Email sent to {len(emails)} subscribers (simulation)")
    return redirect("/admin/dashboard")

# -------------------- Run Server --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7700))
    app.run(debug=False, host="0.0.0.0", port=port)
