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
    # Recipe: 레시피(요리)의 기본 정보로, 영어로 된 요리 이름, 한글로 된 요리 이름, 한글 및 영어로 된 요리 설명
    cursor.execute(
        """
    CREATE TABLE Recipe (
        recipe_id TEXT PRIMARY KEY,
        recipe_name TEXT NOT NULL,
        recipe_name_kr TEXT NOT NULL,
        recipe_desc TEXT NOT NULL
    )
    """
    )

    # Category: 식재료의 종류를 분류하기 위한 카테고리
    cursor.execute(
        """
    CREATE TABLE Category (
        category_id TEXT PRIMARY KEY,
        category_name TEXT NOT NULL
    )
    """
    )

    # IngredientType: 카테고리별 식재료의 설명으로, 영어로 된 식재료 이름, 카테고리 이름, 한글 및 영어로 된 식재료 설명
    cursor.execute(
        """
    CREATE TABLE IngredientType (
        type_id TEXT PRIMARY KEY,
        type_name TEXT NOT NULL,
        category_id TEXT NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES Category(category_id)
    )
    """
    )

    # IngredientProduct: 식재료의 상세 정보로, 식재료 이름, 브랜드 이름, 식재료 양, 식재료 가격, 식재료 평점, 식재료 리뷰 수
    cursor.execute(
        """
    CREATE TABLE IngredientProduct (
        product_id TEXT PRIMARY KEY,
        type_id TEXT NOT NULL,
        name TEXT NOT NULL,
        brand TEXT NOT NULL,
        quantity TEXT NOT NULL,
        price REAL NOT NULL,
        rating REAL NOT NULL,
        review_count INTEGER NOT NULL,
        FOREIGN KEY (type_id) REFERENCES IngredientType(type_id)
    )
    """
    )

    # RecipeIngredient: 레시피별 식재료의 이름, 양
    cursor.execute(
        """
    CREATE TABLE RecipeIngredient (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id TEXT NOT NULL,
        type_id TEXT NOT NULL,
        ingredient_name TEXT NOT NULL,
        quantity TEXT NOT NULL,
        FOREIGN KEY (recipe_id) REFERENCES Recipe(recipe_id),
        FOREIGN KEY (type_id) REFERENCES IngredientType(type_id)
    )
    """
    )

    # RecipeDetail: 레시피의 인원 수, 재료 준비, 조리 방법, 팁
    cursor.execute(
        """
    CREATE TABLE RecipeDetail (
        recipe_id TEXT PRIMARY KEY,
        how_many_people INTEGER NOT NULL,
        preparation_ingredients TEXT NOT NULL,
        cooking_method TEXT NOT NULL,
        tips TEXT,
        FOREIGN KEY (recipe_id) REFERENCES Recipe(recipe_id)
    )
    """
    )

    conn.commit()
    return conn, cursor


##############################################################
#  ✅ Insert the data
##############################################################


# Recipe
def insert_recipes(cursor, recipes):
    for recipe_id, recipe_data in recipes.items():
        # split the recipe name into Korean and English names
        name_parts = recipe_data["name"].split(" (")
        recipe_name_kr = name_parts[0]
        recipe_name = recipe_id  # use the English ID as the recipe name

        cursor.execute(
            "INSERT INTO Recipe VALUES (?, ?, ?, ?)",
            (recipe_id.lower(), recipe_name, recipe_name_kr, recipe_data["desc"]),
        )


# Category
def insert_categories(cursor, ingredients):
    for category_id, category_data in ingredients.items():
        cursor.execute(
            "INSERT INTO Category VALUES (?, ?)", (category_id.lower(), category_id)
        )


# IngredientType
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
                "INSERT INTO IngredientType VALUES (?, ?, ?, ?)",
                (type_id, type_name, category_id.lower(), type_data["desc"]),
            )


# IngredientProduct
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
                    "INSERT INTO IngredientProduct VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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


# RecipeIngredient
def insert_recipe_ingredients(cursor, ingredients, recipes):
    # 우선 type_id를 생성하는 함수 정의
    def get_type_id(name):
        return (
            name.lower()
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace(",", "")
        )

    # 1. ingredients에서 recipe-ingredient 관계 추출
    recipe_ingredients_map = {}

    for category_id, category_data in ingredients.items():
        for type_name, type_data in category_data.items():
            type_id = get_type_id(type_name)

            for recipe in type_data["what_to_use"]:
                recipe_id = recipe.lower()
                if recipe_id not in recipe_ingredients_map:
                    recipe_ingredients_map[recipe_id] = {}

                recipe_ingredients_map[recipe_id][type_name] = type_id

    # 2. recipes에서 상세 재료 정보 추출하여 통합 테이블에 삽입
    for recipe_id, recipe_data in recipes.items():
        if "recipe" not in recipe_data:
            continue

        recipe_id = recipe_id.lower()
        recipe_detail = recipe_data["recipe"]

        for i, (ingredient_name, quantity) in enumerate(
            zip(recipe_detail["ingredients"], recipe_detail["quantity"])
        ):
            # ingredient_name에 해당하는 type_id 찾기
            type_id = get_type_id(ingredient_name)

            cursor.execute(
                "INSERT INTO RecipeIngredient (recipe_id, type_id, ingredient_name, quantity) VALUES (?, ?, ?, ?)",
                (recipe_id, type_id, ingredient_name, quantity),
            )


# 레시피 상세 정보를 추가하는 함수
def insert_recipe_details(cursor, recipes):
    for recipe_id, recipe_data in recipes.items():
        if "recipe" not in recipe_data:
            continue

        recipe_detail = recipe_data["recipe"]

        # RecipeDetails 테이블에 데이터 삽입
        cursor.execute(
            "INSERT INTO RecipeDetail VALUES (?, ?, ?, ?, ?)",
            (
                recipe_id.lower(),
                recipe_detail["how_many_people"],
                recipe_detail["preparation_ingredients"],
                recipe_detail["cooking_method"],
                recipe_detail["tips"],
            ),
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
    insert_recipe_ingredients(cursor, ingredients, recipes)  # recipes 매개변수 추가
    insert_recipe_details(cursor, recipes)

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
        "Recipe",
        "Category",
        "IngredientType",
        "IngredientProduct",
        "RecipeIngredient",
        "RecipeDetail",
    ]
    print("\n--- Validate the data ---")

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")

    # 추가된 검증 쿼리: 불고기 레시피의 상세 정보
    print("\nBulgogi recipe details:")
    cursor.execute(
        """
    SELECT rd.how_many_people, rd.preparation_ingredients, rd.cooking_method, rd.tips 
    FROM RecipeDetail rd
    WHERE rd.recipe_id = 'bulgogi'
    """
    )

    row = cursor.fetchone()
    if row:
        print(f"- 몇 인분: {row[0]}")
        print(f"- 재료 준비: {row[1][:50]}...")
        print(f"- 조리 방법: {row[2][:50]}...")
        print(f"- 팁: {row[3][:50]}...")

    # 변경된 검증 쿼리: 불고기 레시피의 재료와 양 (통합된 테이블 사용)
    print("\nBulgogi recipe ingredients and quantities:")
    cursor.execute(
        """
    SELECT ri.ingredient_name, ri.quantity, it.type_name, it.description
    FROM RecipeIngredient ri
    JOIN IngredientType it ON ri.type_id = it.type_id
    WHERE ri.recipe_id = 'bulgogi'
    """
    )

    for row in cursor.fetchall():
        print(f"- {row[0]} ({row[2]}): {row[1]}")
        print(f"  설명: {row[3][:50]}...")

    # example query: get the recipes that use garlic
    print("\nRecipes that use garlic:")
    cursor.execute(
        """
    SELECT r.recipe_name, r.recipe_name_kr
    FROM Recipe r
    JOIN RecipeIngredient ri ON r.recipe_id = ri.recipe_id
    WHERE ri.type_id = 'garlic'
    """
    )

    for row in cursor.fetchall():
        print(f"- {row[0]} ({row[1]})")

    conn.close()


if __name__ == "__main__":
    main()
