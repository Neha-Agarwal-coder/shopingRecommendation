import pandas as pd

class CustomerAgent:
    def __init__(self, customer_df):
        self.customer_df = customer_df

    def get_customer_profile(self, customer_id):
        customer = self.customer_df[self.customer_df["Customer_ID"] == customer_id]
        return customer.iloc[0].to_dict() if not customer.empty else None
import pandas as pd

class ProductAgent:
    def __init__(self, product_df):
        self.product_df = product_df.copy()

    def score_products_for_customer(self, customer_profile):
        """
        Score each product for a given customer based on weighted features.
        """
        df = self.product_df.copy()
        
        # Match based on browsing and purchase history
        history = customer_profile["Browsing_History"] + customer_profile["Purchase_History"]
        history = [item.lower() for item in history]

        def history_match(row):
            product_tags = (
                str(row["Subcategory"]).lower()
                + " "
                + str(row["Category"]).lower()
                + " "
                + " ".join(eval(row.get("Similar_Product_List", "[]"))).lower()
            )
            return sum(tag in product_tags for tag in history)

        df["history_score"] = df.apply(history_match, axis=1)

        # Normalize numerical columns for fair scoring
        df["Price_norm"] = 1 - (df["Price"] - df["Price"].min()) / (df["Price"].max() - df["Price"].min())
        df["Rating_norm"] = df["Product_Rating"] / 5
        df["Sentiment_norm"] = df["Customer_Review_Sentiment_Score"]
        df["Recommendation_prob"] = df["Probability_of_Recommendation"]

        # Seasonal/Holiday match
        df["season_score"] = (df["Season"] == customer_profile["Season"]).astype(int)
        df["holiday_score"] = (df["Holiday"] == customer_profile["Holiday"]).astype(int)

        # Final weighted score
        df["score"] = (
            1.5 * df["history_score"] +
            1.0 * df["Rating_norm"] +
            1.0 * df["Sentiment_norm"] +
            0.8 * df["Recommendation_prob"] +
            0.5 * df["Price_norm"] +
            0.3 * df["season_score"] +
            0.2 * df["holiday_score"]
        )

        return df.sort_values("score", ascending=False)[["Product_ID", "Category", "Subcategory", "score"]]
    def get_all_products(self):
        return self.product_df

# recommendation_agent.ipynb

import pandas as pd

class RecommendationAgent:
    def __init__(self, customer_agent, product_agent):
        self.customer_agent = customer_agent
        self.product_agent = product_agent

    def recommend_products(self, customer_id, top_n=5, price_weight=1.0, rating_weight=1.0, sentiment_weight=1.0):
        customer_profile = self.customer_agent.get_customer_profile(customer_id)
        if customer_profile is None:
            print(f"Customer {customer_id} not found.")
            return None

        all_products = self.product_agent.get_all_products()

        scored_products = []
        for _, product in all_products.iterrows():
            category_score = 1.0 if product['Category'] in customer_profile['Browsing_History'] else 0.0
            subcategory_score = 1.0 if product['Subcategory'] in customer_profile['Purchase_History'] else 0.0
            price_score = max(0, 1 - abs(product['Price'] - customer_profile['Avg_Order_Value']) / customer_profile['Avg_Order_Value']) * price_weight
            rating_score = product['Product_Rating'] / 5.0 * rating_weight
            sentiment_score = product['Customer_Review_Sentiment_Score'] * sentiment_weight

            final_score = (category_score + subcategory_score + price_score + rating_score + sentiment_score)

            scored_products.append({
                'Product_ID': product['Product_ID'],
                'Category': product['Category'],
                'Subcategory': product['Subcategory'],
                'score': round(final_score, 4)
            })

        scored_df = pd.DataFrame(scored_products)
        top_products = scored_df.sort_values(by='score', ascending=False).head(top_n)

        return top_products


import pandas as pd
import sqlite3

# Load data
customer_df = pd.read_csv("data/customer_data_collection.csv", encoding="utf-8")
product_df = pd.read_csv("data/product_recommendation_data.csv", encoding="utf-8")

# Copy in the class definitions from the above notebooks here too:
# - CustomerAgent
# - ProductAgent
# - RecommendationAgent

# Initialize agents
customer_agent = CustomerAgent(customer_df)
product_agent = ProductAgent(product_df)
recommendation_agent = RecommendationAgent(customer_agent, product_agent)

# Recommend products
customer_id = "C1000"
top_products = recommendation_agent.recommend_products(customer_id, top_n=5)

# Display results
print(f"Top 5 Recommendations for Customer {customer_id}:\n")
print(top_products[['Product_ID', 'Category', 'Subcategory', 'score']] if top_products is not None else "None")

# Save to SQLite
def save_recommendations_to_db(customer_id, recommendations, db_path="smart_shopping.sqlite"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Recommendations (
            Customer_ID TEXT,
            Product_ID TEXT,
            Score REAL
        )
    """)
    for _, row in recommendations.iterrows():
        cursor.execute("""
            INSERT INTO Recommendations (Customer_ID, Product_ID, Score)
            VALUES (?, ?, ?)
        """, (customer_id, row['Product_ID'], row['score']))
    conn.commit()
    conn.close()

if top_products is not None:
    save_recommendations_to_db(customer_id, top_products)

import sqlite3

def save_recommendations_to_db(customer_id, recommended_df, db_path="recommendations.db"):
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            Customer_ID TEXT,
            Product_ID TEXT,
            Category TEXT,
            Subcategory TEXT,
            Score REAL
        )
    ''')
    
    # Add customer_id column if not in DataFrame
    recommended_df = recommended_df.copy()
    recommended_df['Customer_ID'] = customer_id

    # Reorder columns for DB
    db_df = recommended_df[['Customer_ID', 'Product_ID', 'Category', 'Subcategory', 'score']]
    
    # Save to DB
    db_df.to_sql("recommendations", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"✅ Saved {len(recommended_df)} recommendations for {customer_id} to {db_path}.")

# Example call
if top_products is not None and not top_products.empty:
    save_recommendations_to_db(customer_id, top_products)
else:
    print(f"⚠️ No recommendations generated for {customer_id}.")

# Preview saved recommendations
conn = sqlite3.connect("recommendations.db")
saved_recs = pd.read_sql_query("SELECT * FROM recommendations", conn)
conn.close()

print("📋 Preview of saved recommendations:")
display(saved_recs.head(10))
