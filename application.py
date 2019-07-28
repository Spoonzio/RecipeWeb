from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash


from cs50 import SQL
from helpers import login_required

#  Configure application
app = Flask(__name__)

#  Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#  Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///recipes.db")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.methods == "POST":
        term = request.fom.get("search")
        #look up serch term in recipe DB
        result = lookup(term)

        return render_template("search.html" , results=results)

    else:
        if session["user_id"] == None:
            #lookup db info
            return render_template("index.html", info=None)

        else:
            info = db.execute("SELECT name FROM user WHERE id = :iden" :iden = session["user_id"] )
            return render_template("index.html", info=info)

@app.route("/search", methods=["POST", "GET"])
def search():
    if request.methods == "POST":
        term = request.fom.get("search")
        #look up serch term in recipe DB
        result = lookup(term)

        return render_template("search.html" , results=results)

    else:
        return redirect("/")

@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()

    if request.methods == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email:
            return #error message
        elif not password:
            emessage = "missing password"
            return render_template("login.html", emessage=emessage)

        info = db.execute("SELECT * FROM user WHERE email = :email", :email=email)
        if len(info) != 1 or not check_password_hash(info[0]["hash"], password):
            emessage = "invalid email or password"
            return render_template("login.html", emessage=emessage)
        else:
            session["user_id"] = rows[0]["id"]
            return redirect("/")

    else:
        return render_template("login.html", emessage = None)


@app.route("/register")
def register():
    # Register user

    if request.method == "POST":
        # Ensure username was submitted
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")
        compassword = request.form.get("comfirmation")

        if not email:
            emessage = "missing email"
            return render_template("register.html",emessage=emessage)

        # Ensure password was submitted
        elif not password:
            emessage = "missing password"
            return render_template("register.html",emessage=emessage)

        elif not compassword:
            emessage = "confirm password"
            return render_template("register.html",emessage=emessage)

        # Query database for username
        info = db.execute("SELECT * FROM user WHERE email = :email", :email=email)

        if len(info) != 0:
            return apology("user exists already")

        else:
            if password != compassword:
                emessage = "must provide matching password"
                return render_template("register.html",emessage=emessage)

            else:
                hashpw = generate_password_hash(password)
                db.execute("INSERT INTO user ('id','email','hash') VALUES (NULL, :ue, :pw)", ue=email, pw=hashpw)

            # Remember which user has logged in
            rows = db.execute("SELECT * FROM user WHERE email = :email", email=email)
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html", emessage = None)


@app.route("/logout")
def logout():
    # Log user out"""
    # Forget any user_id
    session.clear()

    #  Redirect user to login form
    return redirect("/")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


def lookup(fsearch):
    # lookup db with term
    try:
        result = db.execute("SELECT * FROM recipe WHERE name LIKE '%:search%'", :search=str(fsearch))
        return (result)
    except(KeyError, TypeError, ValueError):
        return (None)

if __name__ == '__main__':
    app.run(debug=True)