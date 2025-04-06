import pandas as pd

from sklearn.preprocessing import MinMaxScaler

class ProductAgent:
    def __init__(self, product_df):
        self.product_df = product_df.copy()
        self.scaler = MinMaxScaler()
        self._prepare_features()

    def _prepare_features(self):
        # Normalize price and rating
        if 'Price' in self.product_df.columns:
            self.product_df['Normalized_Price'] = self.scaler.fit_transform(
                self.product_df[['Price']]
            )
        else:
            self.product_df['Normalized_Price'] = 0.5

        if 'Product_Rating' in self.product_df.columns:
            self.product_df['Normalized_Rating'] = self.scaler.fit_transform(
                self.product_df[['Product_Rating']]
            )
        else:
            self.product_df['Normalized_Rating'] = 0.5

    def get_all_products(self):
        return self.product_df
