import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

def run_eclat(data, min_support, min_confidence, min_lift):
    # Pastikan semua baris dalam fungsi ini menjorok (pakai 4 spasi atau 1 tab)
    basket = data.groupby(['Transaction', 'Item'])['Item'].count().unstack().reset_index().fillna(0).set_index('Transaction')
    basket = basket.applymap(lambda x: 1 if x > 0 else 0)

    frequent_items = apriori(basket, min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_items, metric="lift", min_threshold=min_lift)
    rules = rules[(rules['confidence'] >= min_confidence)]

    return rules
