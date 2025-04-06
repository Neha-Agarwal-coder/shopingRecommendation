import streamlit as st
import pandas as pd
import sqlite3
from customer_agent import CustomerAgent
from product_agent import ProductAgent
from recommendation_agent import RecommendationAgent

# Load datasets
customer_df = pd.read_csv("data/customer_data_collection.csv", encoding="utf-8")
product_df = pd.read_csv("data/product_recommendation_data.csv", encoding="utf-8")

# Initialize agents
customer_agent = CustomerAgent(customer_df)
product_agent = ProductAgent(product_df)
recommendation_agent = RecommendationAgent(customer_agent, product_agent)

# SQLite setup
conn = sqlite3.connect("data/recommendations.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS recommendations (
                    Customer_ID TEXT,
                    Product_ID TEXT,
                    Category TEXT,
                    Subcategory TEXT,
                    Score REAL
                )''')
conn.commit()

# Sidebar: Preferences
st.title("🛍️ Smart Shopping Product Recommender")

st.sidebar.header("🔧 Customize Your Preferences")
selected_customer_id = st.sidebar.selectbox("Select Customer ID", customer_df["Customer_ID"].unique())
price_weight = st.sidebar.slider("Price Sensitivity", 0.0, 1.0, 0.3)
rating_weight = st.sidebar.slider("Rating Importance", 0.0, 1.0, 0.3)
sentiment_weight = st.sidebar.slider("Sentiment Influence", 0.0, 1.0, 0.4)

top_products = pd.DataFrame()

if st.sidebar.button("Recommend Products"):
    top_products = recommendation_agent.recommend_products(
        selected_customer_id,
        top_n=5,
        price_weight=price_weight,
        rating_weight=rating_weight,
        sentiment_weight=sentiment_weight
    )

    if top_products is not None and not top_products.empty:
        st.subheader(f"🎯 Top 5 Recommendations for Customer {selected_customer_id}")
        st.dataframe(top_products[["Product_ID", "Category", "Subcategory", "Price", "Product_Rating", "score"]])

        for _, row in top_products.iterrows():
            cursor.execute("INSERT INTO recommendations (Customer_ID, Product_ID, Category, Subcategory, Score) VALUES (?, ?, ?, ?, ?)", 
                           (selected_customer_id, row["Product_ID"], row["Category"], row["Subcategory"], row["score"]))
        conn.commit()
    else:
        st.warning("⚠️ No recommendations found.")

# Tabs for deeper insights
tab1, tab2, tab3 = st.tabs(["🔁 Similar Items", "📈 Trending", "💡 You Might Like"])

with tab1:
    st.subheader("🔁 Similar Items")
    if not top_products.empty:
        categories = top_products['Category'].unique()
        subcategories = top_products['Subcategory'].unique()
        similar_items = product_df[
            (product_df['Category'].isin(categories)) &
            (product_df['Subcategory'].isin(subcategories))
        ].drop_duplicates().head(10)
        st.dataframe(similar_items[["Product_ID", "Category", "Subcategory", "Price", "Product_Rating"]])
    else:
        st.info("ℹ️ Get recommendations first to view similar items.")

with tab2:
    st.subheader("📈 Trending")
    cursor.execute('''SELECT Product_ID, Category, Subcategory, COUNT(*) as freq
                      FROM recommendations
                      GROUP BY Product_ID
                      ORDER BY freq DESC
                      LIMIT 10''')
    trending = pd.DataFrame(cursor.fetchall(), columns=["Product_ID", "Category", "Subcategory", "Frequency"])
    trending = trending.merge(product_df, on=["Product_ID", "Category", "Subcategory"], how="left")
    st.dataframe(trending[["Product_ID", "Category", "Subcategory", "Price", "Product_Rating", "Frequency"]])

with tab3:
    st.subheader("💡 You Might Like")
    import random
    suggestions = product_df.sample(n=10, random_state=random.randint(0, 9999))
    st.dataframe(suggestions[["Product_ID", "Category", "Subcategory", "Price", "Product_Rating"]])

# Sidebar: View saved
st.sidebar.markdown("---")
st.sidebar.subheader("📂 View Saved Recommendations")

cursor.execute("SELECT DISTINCT Customer_ID FROM recommendations")
customer_ids = [row[0] for row in cursor.fetchall()]
selected_view_id = st.sidebar.selectbox("Select Customer to View", customer_ids)

if st.sidebar.button("View Saved Recommendations"):
    saved_df = pd.read_sql_query("SELECT * FROM recommendations WHERE Customer_ID = ?", conn, params=(selected_view_id,))
    if not saved_df.empty:
        st.subheader(f"📦 Saved Recommendations for {selected_view_id}")
        st.dataframe(saved_df)
    else:
        st.info("ℹ️ No saved recommendations found.")

conn.close()
