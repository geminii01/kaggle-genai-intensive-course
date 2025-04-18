# Capstone Project

## Data Generation
```bash
cd ./capstone-2025q1
source $(poetry env info --path)/bin/activate
python ./data-generation.py
python ./data-to-sql.py
```

- Generate the data and save it to the [`./data`](./data) folder. [🔗](./data-generation.py)

    - [`./data/recipes_{YYYYMMDD}.json`](./data/recipes_{YYYYMMDD}.json)

    - [`./data/ingredients_{YYYYMMDD}.json`](./data/ingredients_{YYYYMMDD}.json)

- Convert the data to the SQLite database. [🔗](./data-to-sql.py)

    - [`./data/data_{YYYYMMDD}.db`](./data/data_{YYYYMMDD}.db)

## Database Table Details

![Database Schema](./assets/dbdiagram.png)

-   데이터베이스는 정보를 체계적으로 정리하기 위해 여러 개의 **표(Table)** 로 데이터를 나누어 저장합니다. 각 표는 특정 주제에 대한 정보만 담고 있고, 서로 필요한 정보를 연결(관계)해서 사용합니다. 이 데이터베이스에는 총 5개의 테이블이 있습니다.<br>The database is designed to organize information systematically by dividing data into multiple **tables**. Each table contains information about a specific topic and uses connections (relationships) to link related information. This database contains a total of 5 tables.

- [link](https://dbdiagram.io/d/680236c61ca52373f57d7030)

### 1. `Recipes` Table

#### Purpose

-   이 테이블은 제공하는 여러 가지 **한식 레시피** 자체에 대한 정보를 저장하는 곳입니다.<br>This table stores information about various **Korean recipes** provided.

#### Columns (Columns of the table)

-   `recipe_id` (TEXT, **PK**): 각 레시피를 구별하는 고유한 **텍스트** 이름표입니다 (예: `"kimchijjigae"`, `"bulgogi"`). 이 값은 절대 중복되지 않으며, 레시피를 식별하는 **기본 키(Primary Key, PK)**입니다.<br>This is a unique **text** identifier (e.g., `"kimchijjigae"`, `"bulgogi"`) to distinguish each recipe. This value is unique and serves as the **primary key (PK)**.
-   `recipe_name` (TEXT): 레시피의 영어/로마자 이름입니다 (현재 스크립트에서는 `recipe_id`와 동일).<br>This is the English/Romanized name of the recipe (currently the same as `recipe_id`).
-   `recipe_name_kr` (TEXT): 레시피의 한글 이름입니다 (예: `"김치찌개"`).<br>This is the Korean name of the recipe (e.g., `"Kimchijjigae"`).
-   `recipe_desc` (TEXT): 해당 레시피가 어떤 음식인지 설명하는 글입니다 (한글/영어 포함).<br>This is a description of what kind of food the recipe is (includes Korean and English).

#### Example data

-   `'bulgogi'`, `'Bulgogi'`, `'불고기'`, `'간장, 꿀, ... 구워 먹는다.'`

#### Connection

-   이 테이블의 `recipe_id`는 `RecipeIngredients` 테이블에서 어떤 레시피에 어떤 재료가 필요한지 연결할 때 사용됩니다.<br>This `recipe_id` is used in the `RecipeIngredients` table to link recipes to their required ingredients.

### 2. `Categories` Table

#### Purpose

-   식료품 가게의 상품들을 큰 **분류(카테고리)**로 나누기 위한 테이블입니다. 예를 들어 '채소류', '육류', '조미료류' 같은 큰 그룹 정보를 관리합니다.<br>This table is used to categorize products in a grocery store into large **categories**. For example, it manages information about large groups such as 'vegetables', 'meats', and 'seasonings'.

#### Columns (Columns of the table)

-   `category_id` (TEXT, **PK**): 각 카테고리를 구별하는 고유한 **텍스트** 이름표입니다 (예: `"vegetables"`, `"meats"`). **기본 키(PK)**입니다.<br>This is a unique **text** identifier (e.g., `"vegetables"`, `"meats"`) to distinguish each category. This value is unique and serves as the **primary key (PK)**.
-   `category_name` (TEXT): 화면에 보여줄 카테고리의 실제 이름입니다 (예: `"Vegetables"`).<br>This is the actual name of the category to be displayed on the screen (e.g., `"Vegetables"`).

#### Example data

-   `'vegetables'`, `'Vegetables'`

#### Connection

-   이 테이블의 `category_id`는 `IngredientTypes` 테이블에서 각 재료 종류가 어떤 카테고리에 속하는지 알려줄 때 사용됩니다.<br>This `category_id` is used in the `IngredientTypes` table to indicate which category each ingredient type belongs to.

### 3. `IngredientTypes` Table

#### Purpose

-   개별 상품이 아니라, **식재료의 종류** 자체(예: '마늘', '돼지 삼겹살')에 대한 정보를 저장합니다.<br>This table stores information about the **type of ingredients** (e.g., 'garlic', 'pork belly') rather than individual products.

#### Columns (Columns of the table)

-   `type_id` (TEXT, **PK**): 각 식재료 종류를 구별하는 고유한 **텍스트** 이름표입니다 (예: `"garlic"`, `"pork_belly"`). 이름에서 자동으로 생성되며, **기본 키(PK)**입니다.<br>This is a unique **text** identifier (e.g., `"garlic"`, `"pork_belly"`), automatically generated from the name, to distinguish each ingredient type. This value is unique and serves as the **primary key (PK)**.
-   `type_name` (TEXT): 화면에 보여줄 식재료 종류의 이름입니다 (예: `"Garlic"`, `"Pork Belly"`).<br>This is the name of the ingredient type to be displayed on the screen (e.g., `"Garlic"`, `"Pork Belly"`).
-   `category_id` (TEXT, **FK**): 이 식재료가 어떤 카테고리에 속하는지를 알려주는 정보입니다. `Categories` 테이블의 `category_id` 값을 참조하는 **외래 키(Foreign Key, FK)**입니다. 예를 들어, 'garlic'의 `category_id`가 'vegetables' 라면, 마늘이 채소류 카테고리에 속한다는 뜻입니다.<br>This indicates which category the ingredient type belongs to. It is a **foreign key (FK)** that references the `category_id` in the `Categories` table. For example, if the `category_id` for 'garlic' is 'vegetables', it means garlic belongs to the vegetables category.
-   `description` (TEXT): 해당 식재료 종류에 대한 설명입니다 (한글/영어 포함).<br>This is a description of the type of ingredient (includes Korean and English).

#### Example data

-   `'garlic'`, `'Garlic'`, `'vegetables'`, `'한국 요리의 필수품! ... 풍미를 더해줘요.'`

#### Connection

-   `category_id` (FK)를 통해 `Categories` 테이블과 연결됩니다 (어떤 카테고리에 속하는지).<br>Connects to the `Categories` table via `category_id` (FK) (indicates which category it belongs to).
-   `type_id` (PK)는 다른 테이블에서 참조됩니다:<br>The `type_id` (PK) is referenced by other tables:
    -   `Products` 테이블: 각 상품이 어떤 종류인지 알려줍니다.<br>`Products` table: Indicates the type of each product.
    -   `RecipeIngredients` 테이블: 레시피에 필요한 재료 종류를 지정합니다.<br>`RecipeIngredients` table: Specifies the ingredient types needed for recipes.

### 4. `Products` Table

#### Purpose

-   실제로 **판매하는 개별 식재료 상품**들의 상세 정보를 저장합니다. (예: 'A사 깐마늘 100g', 'B사 유기농 배 1개')<br>This table stores detailed information about **individual ingredient products** available for sale (e.g., 'Brand A Peeled Garlic 100g', 'Brand B Organic Pear 1ea').

#### Columns (Columns of the table)

-   `product_id` (TEXT, **PK**): 각 판매 상품을 구별하는 고유한 **텍스트** 이름표입니다 (예: `"vegetable-garlic-0"`). **기본 키(PK)**입니다.<br>This is a unique **text** identifier (e.g., `"vegetable-garlic-0"`) to distinguish each product item. This value is unique and serves as the **primary key (PK)**.
-   `type_id` (TEXT, **FK**): 이 상품이 어떤 **종류**의 식재료인지를 알려줍니다. `IngredientTypes` 테이블의 `type_id` 값을 참조하는 **외래 키(FK)**입니다 (예: `'garlic'`).<br>Indicates what **type** of ingredient this product is. It is a **foreign key (FK)** referencing the `type_id` in the `IngredientTypes` table (e.g., `'garlic'`).
-   `name` (TEXT): 상품의 실제 이름입니다 (예: `"Fresh Garlic"`).<br>This is the actual name of the product (e.g., `"Fresh Garlic"`).
-   `brand` (TEXT): 상품의 브랜드 이름입니다 (예: `"Organic Choice"`).<br>This is the brand name of the product (e.g., `"Organic Choice"`).
-   `quantity` (TEXT): 상품의 양이나 개수입니다 (예: `"100g"`, `"1ea"`).<br>This is the quantity or count of the product (e.g., `"100g"`, `"1ea"`).
-   `price` (REAL): 상품의 가격입니다 (숫자).<br>This is the price of the product (number).
-   `rating` (REAL): 고객 평점입니다 (숫자).<br>This is the customer rating (number).
-   `review_count` (INTEGER): 상품 리뷰 개수입니다 (숫자).<br>This is the number of product reviews (number).

#### Example data

-   `'vegetable-garlic-0'`, `'garlic'`, `'Fresh Garlic'`, `'Organic Choice'`, `'100g'`, `2.5`, `2.3`, `95`

#### Connection

-   `type_id` (FK)를 통해 `IngredientTypes` 테이블과 연결되어, 이 상품이 '마늘' 종류라는 것을 알 수 있습니다.<br>Connects to the `IngredientTypes` table via `type_id` (FK), allowing us to know, for example, that this product is of the 'garlic' type.

### 5. `RecipeIngredients` Table

#### Purpose

-   **연결(Linking) 테이블**입니다. `Recipes` 테이블과 `IngredientTypes` 테이블을 서로 이어주는 **다리** 역할을 합니다. 하나의 레시피는 여러 재료 종류를 필요로 하고, 하나의 재료 종류는 여러 레시피에 사용될 수 있는 **다대다(Many-to-Many)** 관계를 표현합니다.<br>This table is a **linking table** that acts as a bridge connecting the `Recipes` table and the `IngredientTypes` table. It represents the **many-to-many (M:N)** relationship where one recipe requires multiple ingredient types, and one ingredient type can be used in multiple recipes.

#### Columns (Columns of the table)

-   `recipe_id` (TEXT, **PK 일부**, **FK**): 어떤 레시피에 대한 정보인지를 나타냅니다. `Recipes` 테이블의 `recipe_id`를 참조하는 **외래 키(FK)**이면서, 아래 `type_id`와 함께 **복합 기본 키(Composite PK)**를 구성합니다.<br>Indicates which recipe this entry is about. It is a **foreign key (FK)** referencing `Recipes.recipe_id` and also part of the **composite primary key (Composite PK)** along with `type_id` below.
-   `type_id` (TEXT, **PK 일부**, **FK**): 어떤 재료 종류에 대한 정보인지를 나타냅니다. `IngredientTypes` 테이블의 `type_id` 값을 참조하는 **외래 키(FK)**이면서, 위 `recipe_id`와 함께 **복합 기본 키(Composite PK)**를 구성합니다.<br>Indicates which ingredient type this entry is about. It is a **foreign key (FK)** referencing `IngredientTypes.type_id` and also part of the **composite primary key (Composite PK)** along with `recipe_id` above.

#### Primary Key (Composite Key)

-   이 테이블에서는 `recipe_id`와 `type_id` **두 개를 합쳐서** 기본 키로 사용합니다. 이는 특정 레시피에 특정 재료가 딱 한 번만 기록되도록 보장합니다. (예: ('bulgogi', 'garlic') 조합은 유일함).<br>This table uses the combination of `recipe_id` and `type_id` as the primary key. This ensures that a specific recipe and ingredient combination is recorded only once (e.g., the ('bulgogi', 'garlic') combination is unique).

#### Example data

-   Need garlic for bulgogi: `('bulgogi', 'garlic')`
-   Need onion for bulgogi: `('bulgogi', 'onion')`
-   Need green onion for kimchijjigae: `('kimchijjigae', 'green_onion')`

#### Connection

-   `recipe_id` (FK)를 통해 `Recipes` 테이블과 연결됩니다.<br>Connects to the `Recipes` table via `recipe_id` (FK).
-   `type_id` (FK)를 통해 `IngredientTypes` 테이블과 연결됩니다.<br>Connects to the `IngredientTypes` table via `type_id` (FK).
-   이 테이블 덕분에 "불고기 레시피에 필요한 재료 목록"이나 "마늘을 사용하는 레시피 목록" 같은 정보를 쉽게 찾을 수 있습니다.<br>This table makes it easy to find information such as "the list of ingredients needed for the bulgogi recipe" or "the list of recipes using garlic".

## Data Source

- 행정안전부 - 공공데이터포털 (Ministry of the Interior and Safety - Open Government Data portal) : https://www.data.go.kr/en/data/15129784/fileData.do
- 한식진흥원 (Korean Food Promotion Institute) : https://www.hansik.or.kr/main/main.do?language=en_US