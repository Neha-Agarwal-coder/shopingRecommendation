import pandas as pd

class CustomerAgent:
    def __init__(self, customer_df):
        self.customer_df = customer_df

    def get_customer_profile(self, customer_id):
        customer = self.customer_df[self.customer_df['Customer_ID'] == customer_id]
        if customer.empty:
            return None
        return customer.iloc[0].to_dict()

    def get_customer_segment(self, customer_id):
        profile = self.get_customer_profile(customer_id)
        if not profile:
            return None
        return profile.get("Customer_Segment", None)
