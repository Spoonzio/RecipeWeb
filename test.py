from cs50 import SQL

db = SQL("sqlite:///recipe.db")

term =str(input("search term: ")).title()

fcategory = [elem['Category'] for elem in db.execute("SELECT DISTINCT Category FROM recipes")]
dcategory = [elem['Alcoholic'] for elem in db.execute("SELECT DISTINCT Alcoholic FROM drinks")]
if term in fcategory:
    result = db.execute("SELECT * FROM recipes WHERE Category = :term ", term=term)
elif term in dcategory:
    result = db.execute("SELECT * FROM drinks WHERE Alcoholic = :term ", term=term)
elif term == "meal":
    result = db.execute("SELECT * FROM recipes WHERE NOT Category = 'Dessert' AND NOT Category = 'Side' AND NOT Category = 'Starter'")
else:
    try:
        result = db.execute("SELECT * FROM recipes WHERE Meal = :term  ", term=term)

    except(KeyError, TypeError, ValueError):
        result = None

print(str(result))