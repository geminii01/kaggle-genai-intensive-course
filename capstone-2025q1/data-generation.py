import os
import time
import json
import random
import warnings
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=True)
warnings.filterwarnings("ignore")


##############################################################
#  ✅ Set random seed
##############################################################

seed = 42
random.seed(seed)
print(f"... Set Random Seed. (Seed: {seed})")


##############################################################
#  ✅ Already have the data
##############################################################

ingredients_path = f"./data/ingredients_{time.strftime('%Y%m%d')}.json"
recipes_path = f"./data/recipes_{time.strftime('%Y%m%d')}.json"

if os.path.exists(ingredients_path) and os.path.exists(recipes_path):
    with open(ingredients_path, "r", encoding="utf-8") as f:
        all_ingredients = json.load(f)
    with open(recipes_path, "r", encoding="utf-8") as f:
        recipes = json.load(f)
    print(
        f"... Data already exists. (Ingredient: {ingredients_path}, Recipe: {recipes_path})"
    )
    exit()


##############################################################
#  ✅ Set up the API key
##############################################################

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print("... Load Google API Key.")


##############################################################
#  ✅ Data Load
##############################################################

hansik_recipes = pd.read_excel(
    "./data/한식메뉴+외국어표기+길라잡이+800선(최종본).xlsx", header=1
)
print("... Load Hansik Recipes.")


##############################################################
#  ✅ Data Preprocessing
##############################################################

# Extract necessary parts
hansik_recipes.columns = hansik_recipes.iloc[0]
hansik_recipes = hansik_recipes.iloc[1:, 4:9]

# Extract 3 Korean recipes and save them
conds = ["김치찌개", "불고기", "떡볶이"]
print(f"... Extract 3 Korean recipes. (Conditions: {conds})")

df = None
for cond in conds:
    df = pd.concat([df, hansik_recipes[hansik_recipes["요리명"] == cond]])

print(f"... Preprocessing Done. (Data Shape: {hansik_recipes.shape} -> {df.shape})")

# change the column names
df.columns = [
    "라틴어 발음",
    "요리명(한국어)",
    "설명(한국어)",
    "요리명(영어)",
    "설명(영어)",
]

# after checking the df, set up the ingredients
recipe_list = [
    {
        "how_many_people": 4,
        "ingredients": [
            "Ripe Cabbage Kimchi (for broth)",
            "Pork Belly",
            "Cooking Oil",
            "Water (500ml)",
            "Tofu",
            "Green Onion",
            "Soy Sauce (for broth)",
            "Sugar",
            "Salt",
        ],
        "quantity": [
            "100g",
            "200g",
            "4Tbsp",
            "1L",
            "300g",
            "45g",
            "2Tbsp",
            "1Tbsp",
            "a little",
        ],
        "preparation_ingredients": """1. Prepare well-fermented Ripe Cabbage Kimchi (for broth) and cut them into 4cm pieces.
2. Slice the Pork Belly thinly across the grain and cut into 4cm pieces.
3. Cut the Tofu into 4x3x1cm thick pieces.
4. Slice the Green Onion into 3cm long pieces.
""",
        "cooking_method": """1. In a large saucepan, heat the Cooking Oil over high heat, stir-fry the Pork Belly until browned. Add the Kimchi and continue stir-frying.
2. Add Water into the saucepan and simmer for 20 minutes. When the Kimchi is tender, add the Tofu, Green Onion, Sugar and Soy Sauce. Cook for 10 more minutes. Season to taste with additional Salt if necessary.
""",
        "tips": "Anchovy broth is sometimes used instead of pork or beef. Also, cook it as little or as much according to your flavor preference.",
    },
    {
        "how_many_people": 4,
        "ingredients": [
            "Beef Sirloin",
            "Onion",
            "Shiitake Mushroom",
            "Green Onion",
            "Cooking Oil",
            "Soy Sauce (for side dishes)",
            "Sugar",
            "Garlic",
            "Sesame Seed Oil",
            "Black Pepper",
            "Ground Sesame Seed",
            "Pear",
            "Cheongju",
        ],
        "quantity": [
            "500g",
            "200g",
            "90g",
            "60g",
            "1Tbsp",
            "5Tbsp",
            "3Tbsp",
            "1Tbsp",
            "1Tbsp",
            "0.5Tbsp",
            "1Tbsp",
            "150g",
            "2Tbsp",
        ],
        "preparation_ingredients": """1. Cut the Beef Sirloin into thin slices 0.2cm thick across the grain, or have butcher slice meat for you. If necessary, cut into smaller bite-size pieces. Pat meat dry with paper towels to remove excess blood.
2. Cut the Onion into long thin slices.
3. Cut the Shiitake Mushroom into thin slices.
4. Slice the Green Onion into 4cm long pieces.
5. Grate the pear and combine with all seasonings of the marinade for beef and mix well in a big bowl.
6. Add the beef to the marinade and toss meat so marinade coats all of the meat. Let it stand about 20 minutes.
7. Add Onion, Green Onion and Shiitake Mushroom and mix well.
""",
        "cooking_method": "Pan fry the beef in a small amount of cooking oil until tender over the high heat.",
        "tips": "In general, bulgogi is made from ribeye sirloin, tenderloin or strip loin. Add fruits juices such as pears or apples to the marinade sauce to make the meat more tender.",
    },
    {
        "how_many_people": 4,
        "ingredients": [
            "Rice Cake",
            "Fish Cake",
            "Water (500ml)",
            "Gochujang",
            "Soy Sauce (for side dishes)",
            "Sugar",
            "Starch Syrup",
        ],
        "quantity": [
            "500g",
            "150g",
            "360ml",
            "3Tbsp",
            "0.5Tbsp",
            "2Tbsp",
            "1Tbsp",
        ],
        "preparation_ingredients": """1. Rinse the soft rice cake sticks and drain. If the rice cake is hard, blanch in boiling water until soft.
2. Cut the fish cakes into 5x2.5cm strips. Place the fish cake strips in a sieve and pour the boiling water over them for degreasing.
""",
        "cooking_method": """1. In a saucepan, add Water, Gochujang, Soy Sauce, Sugar and Starch Syrup and mix them together.
2. Bring the sauce pan to a medium heat, and cook the rice cakes, stir occasionally with a wooden spoon.
3. Add fish cakes, and continue cooking until sauce thickens.
""",
        "tips": "Use a rich brew of anchovies and kelp instead of water to make the dish tastier. More gochut-garu (red chili pepper powder) and additional ingredients such as onion, carrot, and green onion can be added if a spicier taste is preferred.",
    },
]

recipes = {}
for idx in range(df.shape[0]):
    dishName = f"{df.iloc[idx, 1]} ({df.iloc[idx, 0]})"
    dishDesc = f"{df.iloc[idx, 2]} ({df.iloc[idx, 4]})"
    recipes[df.iloc[idx, 0]] = {
        "name": dishName,
        "desc": dishDesc,
        "recipe": recipe_list[idx],
    }

with open(recipes_path, "w", encoding="utf-8") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=4)


##############################################################
#  ✅ Data Generation by Category
##############################################################

# create a dictionary to contain all data
items_num = 5
all_ingredients = {}
print("... Initialize all_ingredients.")


##############################################################
#  ✅ Vegetables
##############################################################

# create a dictionary for Category
all_ingredients["Vegetables"] = {}
print("... Initialize Vegetables.")

items = [
    "Garlic",  # 마늘
    "Shiitake Mushroom",  # 표고버섯
    "Oyster Mushroom",  # 느타리버섯
    "Green Onion",  # 대파
    "Onion",  # 양파
]

brands = [
    "Fresh Farm",
    "Organic Choice",
    "Green Valley",
    "Nature's Best",
    "Farmers Market",
    "Healthy Harvest",
]

quantities = ["100g", "200g", "300g", "500g", "1kg", "2kg"]

product_names = [
    "Fresh {item}",
    "Organic {item}",
    "Premium {item}",
    "Local {item}",
]

# description by item
descs = {
    "Garlic": "한국 요리의 필수품! 알싸하면서도 익히면 달큰한 맛이 나며, 음식의 잡내를 잡고 풍미를 더해줘요. (An essential in Korean cooking! Pungent raw, sweet when cooked, it removes unwanted odors and adds deep flavor.)",
    "Shiitake Mushroom": "특유의 깊은 향과 감칠맛이 일품이에요. 쫄깃한 식감이 살아있어 볶음, 찌개 등 다양하게 활용돼요. (Excellent for its unique deep aroma and rich umami. Its chewy texture works well in stir-fries, broth, and more.)",
    "Oyster Mushroom": "부드럽고 촉촉한 식감과 은은한 향이 특징이에요. 다른 재료와 잘 어울려 맛을 해치지 않고 풍성하게 만들어요. (Features a soft, moist texture and subtle fragrance. Pairs well with other ingredients, adding richness without overpowering.)",
    "Green Onion": "시원하고 알싸한 향으로 음식의 느끼함을 잡아주고 개운한 맛을 더해요. 국물 요리에 들어가면 시원함이 배가 돼요. (Its refreshing, sharp aroma cuts through richness and adds a clean taste. Great in soups for extra freshness.)",
    "Onion": "생으로 먹으면 맵지만 익히면 단맛과 감칠맛이 우러나와 요리의 베이스로 많이 사용돼요. (Pungent raw, but releases sweetness and savory notes (umami) when cooked, often used as a flavor base.)",
}

# what to use by item
what_to_uses = {
    "Garlic": ["Bulgogi"],
    "Shiitake Mushroom": ["Bulgogi"],
    "Oyster Mushroom": ["Bulgogi"],
    "Green Onion": ["Kimchijjigae", "Bulgogi"],
    "Onion": ["Bulgogi"],
}

for item in items:
    entries = []
    for i in range(items_num):  # create products for each item
        name = random.choice(product_names).format(item=item)
        quantity = random.choice(quantities)

        # set price by quantity
        if quantity == "100g" or quantity == "200g":
            price = round(random.uniform(1.0, 3.0), 1)
        elif quantity == "300g" or quantity == "500g":
            price = round(random.uniform(3.0, 5.0), 1)
        else:
            price = round(random.uniform(7.0, 10.0), 1)

        entry = {
            "id": f"vegetable-{item.lower().replace(' ', '')}-{i}",
            "name": name,
            "brand": random.choice(brands),
            "quantity": quantity,
            "price": price,
            "rating": round(random.uniform(1.5, 5.0), 1),
            "reviewCount": random.randint(1, 100),
        }
        entries.append(entry)

    all_ingredients["Vegetables"][item] = {
        "desc": descs[item],
        "what_to_use": what_to_uses[item],
        "ingredients": entries,
    }


##############################################################
#  ✅ Fruits
##############################################################

# create a dictionary for Category
all_ingredients["Fruits"] = {}
print("... Initialize Fruits.")

items = [
    "Pear",  # 배
    "Apple",  # 사과
    "Strawberry",  # 딸기
]

brands = [
    "Juice Shop",
    "Fruit Paradise",
    "Fresh Harvest",
    "Organic Fruit",
    "Local Fruit",
]

quantities = ["1ea", "3ea", "5ea", "10ea", "20ea", "30ea"]

product_names = [
    "Fresh {item}",
    "Organic {item}",
    "Premium {item}",
    "Local {item}",
]

# description by item
descs = {
    "Pear": "시원하고 아삭한 식감에 달콤한 과즙이 풍부해요. 고기를 연하게 하고 은은한 단맛을 더할 때 사용해요. (Cool and crisp with abundant sweet juice. Used to tenderize meat and add subtle sweetness, especially in marinades like Bulgogi.)",
    "Apple": "아삭아삭 씹는 맛이 좋고 새콤달콤한 맛이 특징이에요. 그냥 먹어도 맛있고 샐러드나 디저트에 활용돼요. (Satisfyingly crisp with a characteristic sweet-tart flavor. Delicious fresh or in salads and desserts.)",
    "Strawberry": "상큼하고 달콤한 맛과 향긋한 향이 매력적이에요. 비타민C가 풍부해요. (Attractive bright, sweet taste and lovely fragrance. Rich in Vitamin C.)",
}

# what to use by item
what_to_uses = {
    "Pear": ["Bulgogi"],
    "Apple": [],
    "Strawberry": [],
}

for item in items:
    entries = []
    for i in range(items_num):  # create products for each item
        name = random.choice(product_names).format(item=item)
        quantity = random.choice(quantities)

        # set price by quantity
        if quantity == "1ea":
            price = 1
        elif quantity == "3ea" or quantity == "5ea":
            price = round(random.uniform(3.0, 5.0), 1)
        else:
            price = round(random.uniform(15.0, 23.0), 1)

        entry = {
            "id": f"fruit-{item.lower().replace(' ', '')}-{i}",
            "name": name,
            "brand": random.choice(brands),
            "quantity": quantity,
            "price": price,
            "rating": round(random.uniform(1.5, 5.0), 1),
            "reviewCount": random.randint(1, 100),
        }
        entries.append(entry)

    all_ingredients["Fruits"][item] = {
        "desc": descs[item],
        "what_to_use": what_to_uses[item],
        "ingredients": entries,
    }


##############################################################
#  ✅ Meats
##############################################################

# create a dictionary for Category
all_ingredients["Meats"] = {}
print("... Initialize Meats.")

items = [
    "Pork Belly",  # 돼지 삼겹살
    "Ground Beef",  # 다진 소고기
    "Beef Sirloin",  # 등심 소고기
]

brands = [
    "Beef Master",
    "Pork Paradise",
    "Beef & Pork",
    "Local Meat",
]

quantities = ["100g", "200g", "300g", "500g", "1kg", "2kg"]

product_names = [
    "Fresh {item}",
    "Organic {item}",
    "Premium {item}",
    "Local {item}",
]

# description by item
descs = {
    "Pork Belly": "고소한 지방과 쫄깃한 살코기의 조화가 일품이에요. 구워 먹어도 맛있고, 찌개에 넣으면 깊은 국물 맛을 내줘요. (A fantastic mix of savory fat and chewy meat. Delicious grilled, and adds rich depth to stew broths.)",
    "Ground Beef": "부드러운 식감과 고소한 육향이 특징이에요. 볶음밥, 미트볼 등 다양한 요리에 활용하기 좋아요. (Features a soft texture and savory beef flavor. Versatile for use in fried rice, meatballs, and more.)",
    "Beef Sirloin": "부드러운 육질과 풍부한 육즙, 고소한 맛이 특징이에요. 불고기, 스테이크 등 구이 요리에 잘 어울려요. (Known for its tender texture, rich juices, and savory taste. Excellent for grilling, like in Bulgogi or steaks.)",
}

# what to use by item
what_to_uses = {
    "Pork Belly": ["Kimchijjigae"],
    "Ground Beef": [],
    "Beef Sirloin": ["Bulgogi"],
}

for item in items:
    entries = []
    for i in range(items_num):  # create products for each item
        name = random.choice(product_names).format(item=item)
        quantity = random.choice(quantities)

        # set price by quantity
        if quantity == "100g" or quantity == "200g":
            price = round(random.uniform(5.0, 7.0), 1)
        elif quantity == "300g" or quantity == "500g":
            price = round(random.uniform(7.0, 10.0), 1)
        else:
            price = round(random.uniform(15.0, 23.0), 1)

        entry = {
            "id": f"meat-{item.lower().replace(' ', '')}-{i}",
            "name": name,
            "brand": random.choice(brands),
            "quantity": quantity,
            "price": price,
            "rating": round(random.uniform(1.5, 5.0), 1),
            "reviewCount": random.randint(1, 100),
        }
        entries.append(entry)

    all_ingredients["Meats"][item] = {
        "desc": descs[item],
        "what_to_use": what_to_uses[item],
        "ingredients": entries,
    }


##############################################################
#  ✅ Kimchi
##############################################################

# create a dictionary for Category
all_ingredients["Kimchi"] = {}
print("... Initialize Kimchi.")

items = [
    "Ripe Cabbage Kimchi (for broth)",  # 묵은 김치
    "Cabbage Kimchi (for side dishes)",  # 반찬용 김치
]

brands = ["Bibiho", "OurStore"]

quantities = {
    "Ripe Cabbage Kimchi (for broth)": ["1kg", "2kg"],
    "Cabbage Kimchi (for side dishes)": ["100g", "200g", "300g"],
}

product_names = [
    "Fresh {item}",
    "Organic {item}",
    "Premium {item}",
    "Local {item}",
]

# description by item
descs = {
    "Ripe Cabbage Kimchi (for broth)": "푹 익어 깊은 감칠맛과 시큼한 맛이 특징이에요. 찌개를 끓이면 칼칼하고 시원한 국물 맛을 내줘요. (Deeply fermented with complex umami and distinct sourness. Creates a spicy and refreshing broth in stews like Kimchijjigae.)",
    "Cabbage Kimchi (for side dishes)": "아삭한 식감과 매콤하면서 시원한 맛이 좋아요. 밥반찬으로 먹거나 라면과 함께 먹으면 잘 어울려요. (Crisp texture with a spicy, refreshing taste. Great as a side dish (banchan) or paired with ramen.)",
}

# what to use by item
what_to_uses = {
    "Ripe Cabbage Kimchi (for broth)": ["Kimchijjigae"],
    "Cabbage Kimchi (for side dishes)": [],
}

for item in items:
    entries = []
    for i in range(items_num):  # create products for each item
        name = random.choice(product_names).format(item=item)
        quantity = random.choice(quantities[item])

        # set price by quantity
        if quantity == "1kg":
            price = round(random.uniform(30.0, 40.0), 1)
        elif quantity == "2kg":
            price = round(random.uniform(45.0, 55.0), 1)
        else:
            if quantity == "100g" or quantity == "200g":
                price = round(random.uniform(5.0, 7.0), 1)
            else:
                price = round(random.uniform(7.0, 9.0), 1)

        entry = {
            "id": f"kimchi-{item.lower().replace(' ', '')}-{i}",
            "name": name,
            "brand": random.choice(brands),
            "quantity": quantity,
            "price": price,
            "rating": round(random.uniform(1.5, 5.0), 1),
            "reviewCount": random.randint(1, 100),
        }
        entries.append(entry)

    all_ingredients["Kimchi"][item] = {
        "desc": descs[item],
        "what_to_use": what_to_uses[item],
        "ingredients": entries,
    }


##############################################################
#  ✅ Seasonings
##############################################################

# create a dictionary for Category
all_ingredients["Seasonings"] = {}
print("... Initialize Seasonings.")

items = [
    "Soy Sauce (for side dishes)",  # 반찬용 간장
    "Soy Sauce (for broth)",  # 찌개용 간장
    "Gochujang",  # 고추장
    "Ground Sesame Seed",  # 깨소금
    "Starch Syrup",  # 물엿
    "Sugar",  # 설탕
    "Salt",  # 소금
    "Cooking Oil",  # 식용유
    "Sesame Seed Oil",  # 참기름
    "Cheongju",  # 청주
    "Black Pepper",  # 후춧가루
]

brands = [
    "HCJ",
    "Jempio",
    "Saechandle",
]

quantities = ["100g", "200g", "300g", "500g", "1kg", "2kg"]

product_names = [
    "Fresh {item}",
    "Organic {item}",
    "Premium {item}",
    "Local {item}",
]

# description by item
descs = {
    "Soy Sauce (for side dishes)": "짠맛과 감칠맛이 균형을 이루어 무침, 조림 등 반찬의 간을 맞출 때 주로 사용해요. (Balanced salty and savory (umami) flavors. Primarily used for seasoning side dishes (banchan) like seasoned vegetables (namul) or braised items.)",
    "Soy Sauce (for broth)": "맑고 깔끔한 짠맛과 은은한 단맛이 특징이에요. 국이나 찌개의 간을 맞추는 데 사용돼요. (Clear, clean saltiness with a subtle sweetness. Used for seasoning soups and stews.)",
    "Gochujang": "매콤하면서도 짭짤하고 단맛이 어우러진 한국의 대표 발효 장이에요. 떡볶이, 찌개, 비빔밥 등 매운맛을 낼 때 필수적이에요. (Korea's iconic fermented chili paste - spicy, savory, and slightly sweet. Essential for adding heat to dishes like Tteokbokki, stews, and Bibimbap.)",
    "Ground Sesame Seed": "참깨를 볶아 빻아 고소한 향과 맛이 아주 진해요. 음식의 마지막에 뿌려 풍미를 더해요. (Roasted and ground sesame seeds with a rich, nutty aroma and flavor. Sprinkled on top of dishes for extra flavor and garnish.)",
    "Starch Syrup": "단맛과 함께 음식에 윤기를 더해줘요. 조림이나 볶음 요리의 마무리에 사용하면 먹음직스러워 보여요. (Adds sweetness and a glossy sheen. Used at the end of cooking stir-fries or braises to make them look appetizing.)",
    "Sugar": "가장 기본적인 단맛을 내는 조미료예요. 음식의 맛을 부드럽게 하고 다른 맛과 조화를 이루도록 도와줘요. (Basic sweetener. Softens the overall taste and helps balance other flavors in a dish.)",
    "Salt": "음식의 기본적인 짠맛을 내는 역할을 해요. 재료 본연의 맛을 살리고 감칠맛을 끌어올려 줘요. (Provides fundamental saltiness. Enhances the natural flavors of ingredients and draws out umami.)",
    "Cooking Oil": "재료를 볶거나 부칠 때 사용하며, 음식에 고소한 풍미와 부드러움을 더해줘요. (Used for sautéing or pan-frying. Adds richness and prevents sticking.)",
    "Sesame Seed Oil": "볶은 참깨를 압착해 만들어 특유의 매우 고소한 향과 맛이 특징이에요. 무침이나 비빔밥, 요리 마지막에 풍미를 더할 때 사용해요. (Pressed from roasted sesame seeds, with a distinctively strong, nutty aroma and taste. Used in seasoned vegetables (namul), Bibimbap, or drizzled at the end for flavor.)",
    "Cheongju": "맑은 술로, 요리에 사용하면 잡내를 제거하고 은은한 단맛과 풍미를 더해줘요. (Clear rice wine. Used in cooking to remove unwanted odors (especially from meat/fish) and add subtle sweetness and depth.)",
    "Black Pepper": "톡 쏘는 매운맛과 향긋한 향으로 고기의 누린내를 잡고 음식의 맛을 깔끔하게 마무리해줘요. (Pungent heat and fragrant aroma help mask gamey smells and provide a clean finish to dishes.)",
}

# what to use by item
what_to_uses = {
    "Soy Sauce (for side dishes)": ["Bulgogi", "Tteokbokki"],
    "Soy Sauce (for broth)": ["Kimchijjigae"],
    "Gochujang": ["Tteokbokki"],
    "Ground Sesame Seed": ["Bulgogi"],
    "Starch Syrup": ["Tteokbokki"],
    "Sugar": ["Kimchijjigae", "Bulgogi", "Tteokbokki"],
    "Salt": ["Kimchijjigae"],
    "Cooking Oil": ["Kimchijjigae"],
    "Sesame Seed Oil": ["Bulgogi"],
    "Cheongju": ["Bulgogi"],
    "Black Pepper": ["Bulgogi"],
}

for item in items:
    entries = []
    for i in range(items_num):  # create products for each item
        name = random.choice(product_names).format(item=item)
        quantity = random.choice(quantities)

        # set price by quantity
        if quantity == "100g" or quantity == "200g":
            price = round(random.uniform(5.0, 7.0), 1)
        elif quantity == "300g" or quantity == "500g":
            price = round(random.uniform(7.0, 10.0), 1)
        else:
            price = round(random.uniform(15.0, 23.0), 1)

        entry = {
            "id": f"seasoning-{item.lower().replace(' ', '')}-{i}",
            "name": name,
            "brand": random.choice(brands),
            "quantity": quantity,
            "price": price,
            "rating": round(random.uniform(1.5, 5.0), 1),
            "reviewCount": random.randint(1, 100),
        }
        entries.append(entry)

    all_ingredients["Seasonings"][item] = {
        "desc": descs[item],
        "what_to_use": what_to_uses[item],
        "ingredients": entries,
    }


##############################################################
#  ✅ Processed Foods
##############################################################

# create a dictionary for Category
all_ingredients["Processed Foods"] = {}
print("... Initialize Processed Foods.")

items = [
    "Tofu",  # 두부
    "Fish Cake",  # 어묵
    "Rice Cake",  # 떡
]

brands = [
    "HCJ",
    "Jempio",
    "Saechandle",
]

quantities = {
    "Tofu": ["100g", "200g", "300g"],
    "Fish Cake": ["100g", "200g", "300g"],
    "Rice Cake": ["15ea", "20ea", "30ea"],
}

product_names = [
    "Fresh {item}",
    "Organic {item}",
    "Premium {item}",
    "Local {item}",
]

# description by item
descs = {
    "Tofu": "콩으로 만든 부드럽고 담백한 맛이 특징이에요. 찌개에 넣으면 국물 맛이 배어 더욱 맛있어져요. (Made from soybeans with a soft texture and mild, clean flavor. Absorbs broth flavors beautifully in stews.)",
    "Fish Cake": "생선 살로 만들어 쫄깃한 식감과 감칠맛이 좋아요. 떡볶이, 어묵탕 등 다양한 분식과 반찬에 사용돼요. (Made from fish paste, offering a chewy texture and savory (umami) taste. Used in popular dishes like Tteokbokki and fish cake soup (Eomuk-tang).)",
    "Rice Cake": "쌀로 만들어 쫀득쫀득한 식감이 매력적이에요. 떡볶이나 떡국 등 다양한 요리의 주재료로 쓰여요. (Made from rice flour with an appealingly chewy, glutinous texture. A key ingredient in dishes like Tteokbokki and rice cake soup (Tteokguk).)",
}

# what to use by item
what_to_uses = {
    "Tofu": ["Kimchijjigae"],
    "Fish Cake": ["Tteokbokki"],
    "Rice Cake": ["Tteokbokki"],
}

for item in items:
    entries = []
    for i in range(items_num):  # create products for each item
        name = random.choice(product_names).format(item=item)
        quantity = random.choice(quantities[item])

        # set price by quantity
        if quantity == "100g":
            price = round(random.uniform(3.0, 4.0), 1)
        elif quantity == "200g":
            price = round(random.uniform(4.0, 5.5), 1)
        elif quantity == "300g":
            price = round(random.uniform(5.5, 6.5), 1)
        else:
            if quantity == "15ea":
                price = round(random.uniform(5.0, 7.0), 1)
            elif quantity == "20ea":
                price = round(random.uniform(7.0, 9.0), 1)
            else:
                price = round(random.uniform(9.0, 11.0), 1)

        entry = {
            "id": f"processedfood-{item.lower().replace(' ', '')}-{i}",
            "name": name,
            "brand": random.choice(brands),
            "quantity": quantity,
            "price": price,
            "rating": round(random.uniform(1.5, 5.0), 1),
            "reviewCount": random.randint(1, 100),
        }
        entries.append(entry)

    all_ingredients["Processed Foods"][item] = {
        "desc": descs[item],
        "what_to_use": what_to_uses[item],
        "ingredients": entries,
    }


##############################################################
#  ✅ Others
##############################################################

# create a dictionary for Category
all_ingredients["Others"] = {}
print("... Initialize Others.")

items = ["Water (500ml)"]

brands = ["A", "B", "C"]

quantities = ["1ea", "2ea", "3ea"]

product_names = [
    "Fresh {item}",
    "Organic {item}",
    "Premium {item}",
    "Local {item}",
]

# description by item
descs = {
    "Water (500ml)": "찌개, 국 등의 국물을 만들거나 재료를 삶을 때 필수적이에요. (Essential for making broths for stews and soups, or for boiling ingredients.)"
}

# what to use by item
what_to_uses = {"Water (500ml)": ["Kimchijjigae", "Tteokbokki"]}

for item in items:
    entries = []
    for i in range(items_num):  # create products for each item
        name = random.choice(product_names).format(item=item)
        quantity = random.choice(quantities)

        # set price by quantity
        if quantity == "1ea":
            price = round(random.uniform(1.0, 2.0), 1)
        elif quantity == "2ea":
            price = round(random.uniform(2.0, 3.0), 1)
        else:
            price = round(random.uniform(3.0, 4.0), 1)

        entry = {
            "id": f"other-{item.lower().replace(' ', '')}-{i}",
            "name": name,
            "brand": random.choice(brands),
            "quantity": quantity,
            "price": price,
            "rating": round(random.uniform(1.5, 5.0), 1),
            "reviewCount": random.randint(1, 100),
        }
        entries.append(entry)

    all_ingredients["Others"][item] = {
        "desc": descs[item],
        "what_to_use": what_to_uses[item],
        "ingredients": entries,
    }


##############################################################
#  ✅ Save the data
##############################################################

with open(ingredients_path, "w", encoding="utf-8") as f:
    json.dump(all_ingredients, f, ensure_ascii=False, indent=4)

print("--------------------------------")
print(f"... Save Recipes. (Path: {recipes_path})")
print(f"... Save Ingredients. (Path: {ingredients_path})")
print("--------------------------------")
