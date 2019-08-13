from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import json
import random
import re
# import flask and other libaries

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

# Assign DB
db = SQL("sqlite:///recipe.db")


@app.route("/", methods=["GET", "POST"])
def index():
    # Homepage

    # Choose all the available categories
    result = []
    display = []
    cate = db.execute("SELECT DISTINCT Category FROM recipes UNION SELECT DISTINCT Category FROM drinks")
    cate = [cat["Category"] for cat in cate]

    # Shuffle categories order
    random.shuffle(cate)

    # Select 3 categories
    for x in range(3):
        display.append(str(cate[x]))

    # Choose Recipe for the choosen categories
    for i in display:
        temp = db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE Category = :term ORDER BY RANDOM() LIMIT 3", term=i)
        if not temp:
            temp = db.execute("SELECT Category AS '1', Drink AS '2', Thumb AS '3' FROM drinks WHERE Category = :term ORDER BY RANDOM() LIMIT 3", term=i)

        for j in range(len(temp)):
            result.append(temp[j])

    # Return page with random recipes
    return render_template("index.html", result=result)


@app.route("/search", methods=["POST", "GET"])
def search():
    # Search function

    if request.method == "POST":
        # Look up serch term in recipe DB
        result = lookup()
        return render_template("search.html", result=result)

    else:
        # Print out all search results

        term = str(request.args.get("q")).lower()
        if not term:
            # If invalid query
            return redirect("/")

        try:
            # Select all categories
            fcategory = [elem['Category'].lower() for elem in db.execute("SELECT DISTINCT Category FROM recipes")]
            dcategory = [elem['Category'].lower() for elem in db.execute("SELECT DISTINCT Category FROM drinks")]

            # Determine if search term is a category, if not then will search for recipe names
            if term in fcategory:
                result = db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE LOWER(Category) = :search ", search=term)
            elif term in dcategory:
                result = db.execute("SELECT Category AS '1', Drink AS '2', Thumb AS '3' FROM drinks WHERE LOWER(Category) = :search ", search=term)
            elif term == "meal":
                result = db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE NOT Category = 'Dessert' AND NOT Category = 'Side' AND NOT Category = 'Starter'")
            else:
                # Search for food or drinks

                result = db.execute("SELECT * FROM recipes WHERE LOWER(Meal) = :search", search=term)
                return render_template("food.html", result=result)
                if not result:
                    result = db.execute("SELECT * FROM drinks WHERE LOWER(Drink) = :search", search=term)
                    return render_template("drink.html", result=result)
        except(KeyError, TypeError, ValueError):

            # If error occurs, display error page
            result = None
            return render_template("500.html"), 500

        return render_template("search.html", result=result)


@app.route("/save", methods=["POST", "GET"])
def saveto():
    # Save recipe function
    if request.method == "POST":
        if 'user_id' in session:
            # Get recipe name
            food = str(request.args.get("q")).lower()

            # Check if user have saved it already
            temp = checksaved(food)

            if isinstance(temp, list):
                # Save to DB, show success message, refresh page
                db.execute("INSERT INTO saved(id, user, recipe, food) VALUES (NULL, :user, :re, :food)", user=session["user_id"], re=temp[0], food=temp[1])
                flash("Recipe is saved", "success")
                return redirect("/item?q=" + str(food))

            elif temp == None:
                # Show to user that they already have this recipe saved
                flash("Recipe is already saved", "info")
                return redirect("/item?q=" + str(food))

            elif temp == False:
                # Error page
                return render_template("500.html"), 500

        else:
            # If user access this function without loggin in, direct to login page
            return redirect("/login")


@app.route("/drink", methods=["POST", "GET"])
@app.route("/food", methods=["POST", "GET"])
@app.route("/item", methods=["GET", "POST"])
def item():
    # Individual recipe page

    # Get recipe name
    term = str(request.args.get("q")).lower()

    if not term:
        # If there is no input name / invalid query
        return redirect("/")

    if 'user_id' in session:
        # If user is logged in, enable save button
        butt = "Save To Your Account"
        butdisable = "enabled"

    else:
        # If user is not logged in, disable button
        butt = "You Must Be Logged In To Save Recipes"
        butdisable = "disabled"

    # Print page with all details
    result = db.execute("SELECT * FROM recipes WHERE LOWER(Meal) = :term ", term=term)
    if not result:
        try:
            result = db.execute("SELECT * FROM drinks WHERE LOWER(Drink) = :term", term=term)
            steps = step_extract(result)
            return render_template("drink.html", result=result, steps=steps, butt=butt, disabled=butdisable)

        except(KeyError, TypeError, ValueError):

            # If there is no result from drinks and food database
            return render_template("404.html"), 404

    steps = step_extract(result)
    return render_template("food.html", result=result, steps=steps, butt=butt, disabled=butdisable)


@app.route("/saved", methods=["GET", "POST"])
@login_required
def saved():
    # Display page of saved recipes

    if request.method == 'POST':
        # Delete selected recipe from user profile
        selected = str(request.args.get("q"))
        db.execute("DELETE FROM 'saved' WHERE recipe = :sel AND user = :us", us=session['user_id'], sel=selected)

        flash("Successfully deleted from your profile", "success")
        return redirect("/saved")

    else:
        if 'user_id' not in session:
            # If user access without loogin in
            return redirect("/login")
        else:
            # Look up saved recipe
            records = db.execute("SELECT * FROM saved WHERE user = :iden", iden=session["user_id"])
            table = []

            # Filter saved recipe, provide only selected details
            for record in records:
                temp = {}
                if record['food'] == True:
                    meal = db.execute("SELECT idMeal AS '0', Meal AS '1', Category AS '2'  FROM recipes WHERE idMeal = :mealid", mealid=record['recipe'])
                    temp = meal[0]
                    temp['3'] = "Food"
                else:
                    drink = db.execute("SELECT DrinkID AS '0', Drink AS '1', Category AS '2'  FROM drinks WHERE DrinkID = :drinkid", drinkid=record['recipe'])
                    temp = drink[0]
                    temp['3'] = "Drink"

                table.append(temp)

            return render_template("saved.html", table=table)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    # Display page for user to edit info
    if request.method == 'POST':
        # Get input from fields
        email = request.form.get("emailprofile")
        name = request.form.get("nameprofile")
        newpass = request.form.get("newpass")
        newpassre = request.form.get("newpassre")

        # Get current info of user
        userfield = db.execute("SELECT * FROM user WHERE id = :iden", iden=session['user_id'])

        # If no input
        if not name and not newpass and not email:
            flash("No new info has been entered nor changed.", "info")
            return redirect("/profile")

        # Check for email, if exists in DB already
        if email:
            checkemail = db.execute("SELECT id FROM user WHERE email = :em", em=email)
            if not checkemail or (email == userfield[0]['email']):
                userfield[0]['email'] = email
            else:
                flash("Email is already registered, please use another one.", "warning")
                return redirect("/profile")

        # Check if entered passwords match
        if newpass:
            if newpass != newpassre:
                flash("Passwords do not match. Please re-enter to confirm.", "warning")
                return redirect("/profile")
            else:
                userfield[0]['hash'] = generate_password_hash(newpass)

        # Change name if user has entered a name
        if name:
            userfield[0]['name'] = name

        # Update user info to new info
        for user in userfield:
            db.execute("UPDATE user SET name = :name , email = :email, hash = :hashpw WHERE id = :iden", name=user["name"], email=user["email"], hashpw=user["hash"], iden=session["user_id"])

        flash("Successfully updated your profile information", "success")
        return redirect("/profile")
    else:

        # Load page with user info
        info = db.execute("SELECT * FROM user WHERE id = :iden", iden = session["user_id"])
        return render_template("profile.html", info=info[0])


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    # Log in
    if request.method == "POST":
        # Get user inputs
        email = request.form.get("email")
        password = request.form.get("password")

        # Missing fields
        if not email:
            flash("Missing Email", "danger")
            return render_template("login.html"), 400
        elif not password:
            flash("Missing Password", "danger")
            return render_template("login.html"), 400

        # Select user from DB, compare passwords, and see if user exists
        info = db.execute("SELECT * FROM user WHERE email = :email", email=email)
        if len(info) != 1 or not check_password_hash(info[0]["hash"], password):
            # User not found or incorrect password
            flash("Invalid Email Or Password", "danger")
            return render_template("login.html"), 400

        else:
            # Correct email and password
            session["user_id"] = info[0]["id"]
            flash("Logged In Successfully", "success")
            return redirect("/")

    else:
        # Display login page
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
            # Ensure email is entered
            flash("Missing Email", 'danger')
            return render_template("register.html")

        elif not password:
            # Ensure password is entered
            flash("Missing Password", 'danger')
            return render_template("register.html")

        elif not compassword:
            # Ensure comfirmation password is entered
            flash("Please Confirm Password", 'danger')
            return render_template("register.html")

        # Query database for username
        info = db.execute("SELECT * FROM user WHERE email = :email", email=email)

        if len(info) != 0:
            # If DB return something with user info
            flash("User Already Exists", 'danger')
            return render_template("register.html")

        else:
            if password != compassword:
                # Ensure comfirmation password matches
                flash("Must Provide Matching Password", 'danger')
                return render_template("register.html")

            else:
                # Generate hash and insert info into DB
                hashpw = generate_password_hash(password)
                db.execute("INSERT INTO user ('id','name','email','hash') VALUES (NULL,:un, :ue, :pw)", un=name, ue=email, pw=hashpw)

            # Remember which user has logged in
            info = db.execute("SELECT * FROM user WHERE email = :email", email=email)
            session["user_id"] = info[0]["id"]

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/check", methods=["GET"])
def check():

    # Check email if exists when user register, JS
    email = request.args.get("email")
    info = db.execute("SELECT email FROM user WHERE email = :email", email=email)

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
    flash("Logged out successfully", "success")
    return redirect("/")


@app.errorhandler(404)
def page_not_found(e):
    # Return 404 for not found error
    return render_template("404.html"), 404


@app.errorhandler(500)
def page_not_found(e):
    # Return 404 for server error
    return render_template("500.html"), 500


def step_extract(fresult):
    # Extract instruction and format string
    instruction = str(fresult[0]['Instructions'])
    steps = instruction.split(". ")

    return (steps)


def checksaved(reci):
    # Check saved_db if user has saved
    re_id = [elem['idMeal'] for elem in db.execute("SELECT idMeal FROM recipes WHERE LOWER(Meal) = :search", search=reci)]
    food = True

    if not re_id:
        re_id = [elem['DrinkID'] for elem in db.execute("SELECT DrinkID FROM drinks WHERE LOWER(Drink) = :search", search=reci)]
        food = False

        if not re_id:
            return(False)

    # Return recipe details from DB
    exist = db.execute("SELECT * FROM saved WHERE recipe = :re AND user = :user", user=session["user_id"], re=re_id)

    if not exist:
        return([re_id, food])
    else:
        return(None)


def lookup():
    # lookup recipe db with term
    search = request.form.get("search").title()
    result = []
    temp = []

    # Create search condition
    tool = ["%" + str(search), "%" + str(search) + "%", str(search) + "%"]

    for t in tool:
        try:
            # search from drink and food db
            temp.append(db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE Meal LIKE :s ", s=t))
            temp.append(db.execute("SELECT Category AS '1', Drink AS '2', Thumb AS '3' FROM drinks WHERE Drink LIKE :s ", s=t))
        except(KeyError, TypeError, ValueError):
            pass

    # Remove duplicate from the search
    for tlist in temp:
        for d in tlist:
            if d not in result:
                result.append(d)

    return result


if __name__ == '__main__':
    app.run(debug=True)