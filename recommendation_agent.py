import pandas as pd

class RecommendationAgent:
    def __init__(self, customer_agent, product_agent):
        self.customer_agent = customer_agent
        self.product_agent = product_agent

    def recommend_products(self, customer_id, top_n=5, price_weight=0.4, rating_weight=0.4, sentiment_weight=0.0, category_weight=0.2):
        # Get customer profile
        customer_profile = self.customer_agent.get_customer_profile(customer_id)
        if customer_profile is None:
            print(f"Customer {customer_id} not found.")
            return None

        all_products = self.product_agent.get_all_products()
        if all_products.empty:
            print("No products available.")
            return None

        scored_products = []
        for _, product in all_products.iterrows():
            score = 0

            # Price score: lower price is better
            if 'Price' in product and pd.notna(product['Price']):
                price_score = 1 / (product['Price'] + 1)  # avoid div by zero
                score += price_weight * price_score

            # Rating score
            if 'Product_Rating' in product and pd.notna(product['Product_Rating']):
                rating_score = product['Product_Rating'] / 5  # assuming 5 is max rating
                score += rating_weight * rating_score

            # Category matching score
            if 'Category' in product and 'Preferred_Category' in customer_profile:
                category_match = 1 if product['Category'] == customer_profile['Preferred_Category'] else 0
                score += category_weight * category_match

            # You can add sentiment_score here if needed in future
            scored_products.append({
                **product,
                'score': score
            })

        # Sort by score
        scored_df = pd.DataFrame(scored_products)
        scored_df = scored_df.sort_values(by="score", ascending=False).head(top_n)

        return scored_df
