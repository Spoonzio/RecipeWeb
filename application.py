from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import json
import random
import re

from cs50 import SQL
from helper import login_required

#  Configure application
app = Flask(__name__)

#  Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#  Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#assign DB
db = SQL("sqlite:///recipe.db")

@app.route("/", methods=["GET", "POST"])
def index():

    result = []
    display = []
    cate = db.execute("SELECT DISTINCT Category FROM recipes UNION SELECT DISTINCT Category FROM drinks")
    cate = [cat["Category"] for cat in cate]

    random.shuffle(cate)

    for x in range(3):
        display.append(str(cate[x]))

    for i in display:
        temp = db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE Category = :term ORDER BY RANDOM() LIMIT 3", term=i)
        if not temp:
            temp = db.execute("SELECT Category AS '1', Drink AS '2', Thumb AS '3' FROM drinks WHERE Category = :term ORDER BY RANDOM() LIMIT 3", term=i)

        for j in range(len(temp)):
            result.append(temp[j])


    return render_template("index.html", result = result)



@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        #look up serch term in recipe DB
        result = lookup()
        return render_template("search.html", result = result)

    else:
        term = str(request.args.get("q")).lower()
        if not term:
            return redirect("/")

        try:
            fcategory = [elem['Category'].lower() for elem in db.execute("SELECT DISTINCT Category FROM recipes")]
            dcategory = [elem['Category'].lower() for elem in db.execute("SELECT DISTINCT Category FROM drinks")]
            if term in fcategory:
                result = db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE LOWER(Category) = :search ", search=term)
            elif term in dcategory:
                result = db.execute("SELECT Category AS '1', Drink AS '2', Thumb AS '3' FROM drinks WHERE LOWER(Category) = :search ", search=term)
            elif term == "meal":
                result = db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE NOT Category = 'Dessert' AND NOT Category = 'Side' AND NOT Category = 'Starter'")
            else:
                result = db.execute("SELECT * FROM recipes WHERE LOWER(Meal) = :search", search=term)
                return render_template("food.html" , result = result)
                if not result:
                    result = db.execute("SELECT * FROM drinks WHERE LOWER(Drink) = :search", search=term)
                    return render_template("drink.html" , result = result)
        except(KeyError, TypeError, ValueError):
            result = None

        return render_template("search.html" , result = result)


@app.route("/drink", methods=["POST", "GET"])
@app.route("/food", methods=["POST", "GET"])
@app.route("/item", methods = ["GET", "POST"])
def item():
    if request.method == "POST":
        if 'user_id' in session:
            temp = checksaved()

            if isinstance(temp, list):
                db.execute("INSERT INTO saved(id, user, recipe, food) VALUES (NULL, :user, :re, :food)", user = session["user_id"], re = temp[0], food = temp[1])
                flash("Recipe is saved", "success")

            elif temp == None:
                flash("Recipe is already saved", "info")

            elif temp == False:
                return render_template("500.html"), 500

        else:
            return redirect("/login")

    else:
        term = str(request.args.get("q")).lower()

        if not term:
            return redirect("/")

        if 'user_id' in session:
            butt = "Save To Your Account"
            butdisable = "enabled"

        else:
            butt = "You Must Be Logged In To Save Recipes"
            butdisable = "disabled"

        result = db.execute("SELECT * FROM recipes WHERE LOWER(Meal) =  :term ", term = term)
        if not result :
            try:
                result = db.execute("SELECT * FROM drinks WHERE LOWER(Drink) = :term", term = term)
                steps = step_extract(result)

                return render_template("drink.html", result = result, steps = steps, butt = butt, disabled = butdisable)
            except(KeyError, TypeError, ValueError):
                return render_template("404.html"), 404

        steps = step_extract(result)
        return render_template("food.html", result = result, steps = steps, butt = butt, disabled = butdisable)

@app.route("/saved")
@login_required
def saved():
    if 'user_id' not in session:
        return redirect("/")
    else:
        #look up saved recipe
        return render_template("saved.html")


@app.route("/login", methods = ["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email:
            flash("Missing Email", "danger")
            return render_template("login.html"),400
        elif not password:
            flash("Missing Password", "danger")
            return render_template("login.html"),400

        info = db.execute("SELECT * FROM user WHERE email = :email", email=email)
        if len(info) != 1 or not check_password_hash(info[0]["hash"], password):
            flash("Invalid Email Or Password", "danger")
            return render_template("login.html"),400
        else:
            session["user_id"] = info[0]["id"]
            return redirect("/")

    else:
        return render_template("login.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    # Register user
    if request.method == "POST":
        # Ensure username was submitted
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")
        compassword = request.form.get("confirmation")

        if not email:
            flash("Missing Email", 'danger')
            return render_template("register.html")

        # Ensure password was submitted
        elif not password:
            flash("Missing Password", 'danger')
            return render_template("register.html")

        elif not compassword:
            flash("Please Confirm Password", 'danger')
            return render_template("register.html")

        # Query database for username
        info = db.execute("SELECT * FROM user WHERE email = :email", email=email)

        if len(info) != 0:
            flash("User Already Exists", 'danger')
            return render_template("register.html")

        else:
            if password != compassword:
                flash("Must Provide Matching Password", 'danger')
                return render_template("register.html")

            else:
                hashpw = generate_password_hash(password)
                db.execute("INSERT INTO user ('id','name','email','hash') VALUES (NULL,:un, :ue, :pw)",un=name, ue=email, pw=hashpw)

            # Remember which user has logged in
            info = db.execute("SELECT * FROM user WHERE email = :email", email=email)
            session["user_id"] = info[0]["id"]

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html", emessage = None)


@app.route("/check", methods=["GET"])
def check():
    email = request.args.get("email")
    info = db.execute("SELECT email FROM user WHERE email = :email", email = email)

    if not info:
        # if both true which user exists in DB
       return jsonify(True)

    elif email and (info[0]['email'] == email):
        # if both true which user exists in DB
        return jsonify(False)

    else:
        return jsonify(False)

@app.route("/logout")
@login_required
def logout():
    # Log user out
    # Forget any user_id
    session.clear()

    #  Redirect user to login form
    return redirect("/")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

def step_extract(fresult):
    instruction = str(fresult[0]['Instructions'])
    steps = instruction.split(". ")

    return steps


def checksaved():
    term = str(request.args.get("q")).lower()

    re_id = [elem['DrinkID'] for elem in db.execute("SELECT idMeal FROM recipes WHERE LOWER(Meal) = :search", search=term)]
    food = True

    if not re_id:
        re_id = [elem['DrinkID'] for elem in db.execute("SELECT DrinkID FROM drinks WHERE LOWER(Drink) = :search", search=term)]
        food = False

        if not re_id:
            return(False)

    exist = db.execute("SELECT * FROM saved WHERE recipe = :re AND user = :user", user = session["user_id"], re = re_id)

    if exist == None:
        return([re_id, food])
    else:
        return(None)


def lookup():
    # lookup db with term
    search = request.form.get("search").title()

    result =[]
    temp = []
    tool = ["%" + str(search), "%" + str(search) + "%", str(search) + "%"]
    for t in tool:
        try:
            temp.append(db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE Meal LIKE :s ", s = t))
            temp.append(db.execute("SELECT Category AS '1', Drink AS '2', Thumb AS '3' FROM drinks WHERE Drink LIKE :s ", s = t))
        except(KeyError, TypeError, ValueError):
            pass

    for tlist in temp:
        for d in tlist:
            if d not in result:
                result.append(d)

    return result

if __name__ == '__main__':
    app.run(debug=True)