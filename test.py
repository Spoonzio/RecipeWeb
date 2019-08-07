from cs50 import SQL
import random

db = SQL("sqlite:///recipe.db")



# fcategory = [elem['Category'] for elem in db.execute("SELECT DISTINCT Category FROM recipes")]
# dcategory = [elem['Category'] for elem in db.execute("SELECT DISTINCT Category FROM drinks")]
# if term in fcategory:
#     result = db.execute("SELECT * FROM recipes WHERE Category = :term ", term=term)
# elif term in dcategory:
#     result = db.execute("SELECT * FROM drinks WHERE Alcoholic = :term ", term=term)
#     print("T")
# elif term == "meal":
#     result = db.execute("SELECT * FROM recipes WHERE NOT Category = 'Dessert' AND NOT Category = 'Side' AND NOT Category = 'Starter'")
# else:
#     try:
#         result = db.execute("SELECT * FROM recipes WHERE Meal = :term  ", term=term)

#     except(KeyError, TypeError, ValueError):
#         result = None

# print(str(dcategory))




search =str(input("search term: ")).title()

result =[]
temp = []
tool = ["%" + str(search), "%" + str(search) + "%", str(search) + "%"]
for t in tool:
    try:
        temp.append(db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE Meal LIKE :s ", s = t))
    except(KeyError, TypeError, ValueError):
        pass

for tlist in temp:
    for d in tlist:
        if d not in result:
            result.append(d)

print(str(result))



