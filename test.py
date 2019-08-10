from cs50 import SQL
import random

import re

db = SQL("sqlite:///recipe.db")


print(str(db.execute("SELECT DrinkID AS '1' FROM drinks WHERE Drink = 'YOYO'")))

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




# search =str(input("search term: ")).title()

# result =[]
# temp = []
# tool = ["%" + str(search), "%" + str(search) + "%", str(search) + "%"]
# for t in tool:
#     try:
#         temp.append(db.execute("SELECT Category AS '1', Meal AS '2', MealThumb AS '3' FROM recipes WHERE Meal LIKE :s ", s = t))
#     except(KeyError, TypeError, ValueError):
#         pass

# for tlist in temp:
#     for d in tlist:
#         if d not in result:
#             result.append(d)

# print(str(result))



# def step_extract(fresult):
#     instruction = str(fresult[0]['Instructions'])
#     steps = instruction.split(".")

#     return steps



# term = str(input("search term: ")).lower()
# #strip

# result = db.execute("SELECT * FROM recipes WHERE LOWER(Meal) =  :term ", term = term)
# steps = step_extract(result)
# print(str(steps))

# records = db.execute("SELECT * FROM saved WHERE user = '1' ")
# table = []
# print(str(records))

# for record in records:
#     temp = {}
#     if record['food'] == True:
#         meal = db.execute("SELECT Meal AS '1', Category AS '2'  FROM recipes WHERE idMeal = :mealid", mealid = record['recipe'])
#         temp = meal[0]
#         temp['3'] = "Food"
#     else:
#         drink = db.execute("SELECT Drink AS '1', Category AS '2'  FROM drinks WHERE DrinkID = :drinkid", drinkid = record['recipe'])
#         temp = drink[0]
#         temp['3'] = "Drink"

#     table.append(temp)

# print(str(table))





























