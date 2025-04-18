import os
import json
import sqlite3
import time

##############################################################
#  ✅ Set the paths
##############################################################

current_date = time.strftime("%Y%m%d")
ingredients_path = f"./data/ingredients_{current_date}.json"
recipes_path = f"./data/recipes_{current_date}.json"
db_path = f"./data/data_{current_date}.db"


##############################################################
#  ✅ Load the data
##############################################################


def load_json_data():
    with open(ingredients_path, "r", encoding="utf-8") as f:
        ingredients = json.load(f)

    with open(recipes_path, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    return ingredients, recipes


##############################################################
#  ✅ Create the database
##############################################################


def create_database():
    # delete the existing database file
    if os.path.exists(db_path):
        os.remove(db_path)

    # connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # create the tables
    # Recipes
    cursor.execute(
        """
    CREATE TABLE Recipes (
        recipe_id TEXT PRIMARY KEY,
        recipe_name TEXT NOT NULL,
        recipe_name_kr TEXT NOT NULL,
        recipe_desc TEXT NOT NULL
    )
    """
    )

    # Categories
    cursor.execute(
        """
    CREATE TABLE Categories (
        category_id TEXT PRIMARY KEY,
        category_name TEXT NOT NULL
    )
    """
    )

    # IngredientTypes
    cursor.execute(
        """
    CREATE TABLE IngredientTypes (
        type_id TEXT PRIMARY KEY,
        type_name TEXT NOT NULL,
        category_id TEXT NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES Categories(category_id)
    )
    """
    )

    # Products
    cursor.execute(
        """
    CREATE TABLE Products (
        product_id TEXT PRIMARY KEY,
        type_id TEXT NOT NULL,
        name TEXT NOT NULL,
        brand TEXT NOT NULL,
        quantity TEXT NOT NULL,
        price REAL NOT NULL,
        rating REAL NOT NULL,
        review_count INTEGER NOT NULL,
        FOREIGN KEY (type_id) REFERENCES IngredientTypes(type_id)
    )
    """
    )

    # RecipeIngredients
    cursor.execute(
        """
    CREATE TABLE RecipeIngredients (
        recipe_id TEXT,
        type_id TEXT,
        PRIMARY KEY (recipe_id, type_id),
        FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id),
        FOREIGN KEY (type_id) REFERENCES IngredientTypes(type_id)
    )
    """
    )

    conn.commit()
    return conn, cursor


##############################################################
#  ✅ Insert the data
##############################################################


# Recipes
def insert_recipes(cursor, recipes):
    for recipe_id, recipe_data in recipes.items():
        # split the recipe name into Korean and English names
        name_parts = recipe_data["name"].split(" (")
        recipe_name_kr = name_parts[0]
        recipe_name = recipe_id  # use the English ID as the recipe name

        cursor.execute(
            "INSERT INTO Recipes VALUES (?, ?, ?, ?)",
            (recipe_id.lower(), recipe_name, recipe_name_kr, recipe_data["desc"]),
        )


# Categories
def insert_categories(cursor, ingredients):
    for category_id, category_data in ingredients.items():
        cursor.execute(
            "INSERT INTO Categories VALUES (?, ?)", (category_id.lower(), category_id)
        )


# IngredientTypes
def insert_ingredient_types(cursor, ingredients):
    for category_id, category_data in ingredients.items():
        for type_name, type_data in category_data.items():
            # create the type_id by removing special characters and spaces
            type_id = (
                type_name.lower()
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
            )

            cursor.execute(
                "INSERT INTO IngredientTypes VALUES (?, ?, ?, ?)",
                (type_id, type_name, category_id.lower(), type_data["desc"]),
            )


# Products
def insert_products(cursor, ingredients):
    for category_id, category_data in ingredients.items():
        for type_name, type_data in category_data.items():
            # create the type_id
            type_id = (
                type_name.lower()
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
            )

            for product in type_data["ingredients"]:
                cursor.execute(
                    "INSERT INTO Products VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        product["id"],
                        type_id,
                        product["name"],
                        product["brand"],
                        product["quantity"],
                        product["price"],
                        product["rating"],
                        product["reviewCount"],
                    ),
                )


# RecipeIngredients
def insert_recipe_ingredients(cursor, ingredients):
    # create the recipe-ingredient relationships
    recipe_ingredients = set()

    for category_id, category_data in ingredients.items():
        for type_name, type_data in category_data.items():
            type_id = (
                type_name.lower()
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
            )

            for recipe in type_data["what_to_use"]:
                recipe_ingredients.add((recipe.lower(), type_id))

    for recipe_id, type_id in recipe_ingredients:
        cursor.execute(
            "INSERT INTO RecipeIngredients VALUES (?, ?)", (recipe_id, type_id)
        )


# Main
def main():
    print("... Convert JSON data to SQLite database")

    # load the JSON data
    ingredients, recipes = load_json_data()
    print(
        f"... Load the JSON data: {len(recipes)} recipes, {sum(len(category) for category in ingredients.values())} ingredient types"
    )

    # create the database
    conn, cursor = create_database()
    print(f"... Create the database: {db_path}")

    # insert the data
    insert_recipes(cursor, recipes)
    insert_categories(cursor, ingredients)
    insert_ingredient_types(cursor, ingredients)
    insert_products(cursor, ingredients)
    insert_recipe_ingredients(cursor, ingredients)

    # save the changes and close the connection
    conn.commit()
    conn.close()

    print("... Convert the data")

    # validate the data
    validate_data()


# Validate the data
def validate_data():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # check the number of records in each table
    tables = [
        "Recipes",
        "Categories",
        "IngredientTypes",
        "Products",
        "RecipeIngredients",
    ]
    print("\n--- Validate the data ---")

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")

    # example query: get the ingredients needed for the bulgogi recipe
    print("\nBulgogi recipe ingredients:")
    cursor.execute(
        """
    SELECT it.type_name, it.description
    FROM IngredientTypes it
    JOIN RecipeIngredients ri ON it.type_id = ri.type_id
    WHERE ri.recipe_id = 'bulgogi'
    """
    )

    for row in cursor.fetchall():
        print(f"- {row[0]}: {row[1][:50]}...")

    # example query: get the recipes that use garlic
    print("\nRecipes that use garlic:")
    cursor.execute(
        """
    SELECT r.recipe_name, r.recipe_name_kr
    FROM Recipes r
    JOIN RecipeIngredients ri ON r.recipe_id = ri.recipe_id
    WHERE ri.type_id = 'garlic'
    """
    )

    for row in cursor.fetchall():
        print(f"- {row[0]} ({row[1]})")

    conn.close()


if __name__ == "__main__":
    main()
