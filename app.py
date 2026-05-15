import math
import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict

# ---------------------------------------------------------------
# Streamlit Page Configuration
# ---------------------------------------------------------------
st.set_page_config(
    page_title="ECLAT PRODUCT BUNDLING SYSTEM",
    layout="wide"
)

# ================================================================
# Header Utama
# ================================================================
st.title("ECLAT-BASED PRODUCT BUNDLING SYSTEM")
st.markdown("Sistem analisis bundling produk berbasis ECLAT untuk menemukan itemset yang sering muncul dan menghitung confidence & lift.")
st.markdown("---")

# ================================================================
# Sidebar Configuration
# ---------------------------------------------------------------
st.sidebar.header("Pengaturan")
min_support = st.sidebar.slider("Minimum Support", 0.001, 0.5, 0.05, 0.001)
min_confidence = st.sidebar.slider("Minimum Confidence", 0.01, 1.0, 0.5, 0.01)
min_lift = st.sidebar.slider("Minimum Lift", 0.1, 5.0, 1.0, 0.1)

frequent_k = st.sidebar.selectbox("Frequent K-Itemset", [2, 3], index=0)  # Default 2-itemset
select_top_k = st.sidebar.number_input(
    "Top-K Bundling (Support Tertinggi dari Rules Valid)",
    min_value=1, max_value=20, value=10, step=1
)

# ================================================================
# Utility Functions
# ================================================================
def load_transactions_from_df(df: pd.DataFrame) -> list:
    """Fungsi untuk mengubah data transaksi menjadi format yang digunakan ECLAT."""
    transactions = df.groupby('id_transaksi')['nama_produk'].apply(list).tolist()
    return transactions

def build_tid_list(transactions):
    """Membentuk TID List untuk item yang ada dalam transaksi."""
    item_tidset = defaultdict(set)
    for idx, transaction in enumerate(transactions):
        for item in transaction:
            item_tidset[item].add(idx)
    return item_tidset

def eclat(transactions, min_support):
    """Implementasi algoritma ECLAT dengan pendekatan pencarian TID List."""
    item_tidset = build_tid_list(transactions)
    frequent_itemsets = []

    # 1-itemsets: Cek apakah item memenuhi support minimum
    for item, tidset in item_tidset.items():
        if len(tidset) / len(transactions) >= min_support:
            frequent_itemsets.append((frozenset([item]), tidset))

    # Generate 2-itemsets, 3-itemsets, ...
    k = 2
    while True:
        candidate_itemsets = []
        for i in range(len(frequent_itemsets)):
            for j in range(i + 1, len(frequent_itemsets)):
                itemset1, tidset1 = frequent_itemsets[i]
                itemset2, tidset2 = frequent_itemsets[j]
                if len(itemset1.union(itemset2)) == k:
                    new_tidset = tidset1.intersection(tidset2)
                    if len(new_tidset) / len(transactions) >= min_support:
                        candidate_itemsets.append((itemset1.union(itemset2), new_tidset))
        if not candidate_itemsets:
            break
        frequent_itemsets.extend(candidate_itemsets)
        k += 1

    return frequent_itemsets

def calculate_confidence_lift(frequent_itemsets, transactions):
    """Menghitung confidence dan lift untuk aturan asosiasi berdasarkan frequent itemsets."""
    rules = []
    for itemset, tidset in frequent_itemsets:
        if len(itemset) > 1:
            for subset in itemset:
                antecedent = frozenset([subset])
                consequent = itemset - antecedent
                support_antecedent = len(tidset) / len(transactions)
                support_consequent = len(tidset) / len(transactions)
                support_union = len(tidset) / len(transactions)
                confidence = support_union / support_antecedent if support_antecedent > 0 else 0
                lift = confidence / support_consequent if support_consequent > 0 else 0
                if confidence >= min_confidence and lift >= min_lift:
                    if len(itemset) == 2:
                        rules.append({
                            'Produk A': ', '.join(list(antecedent)),
                            'Produk B': ', '.join(list(consequent)),
                            'Support': support_union,
                            'Confidence': confidence,
                            'Lift': lift
                        })
                    elif len(itemset) == 3:
                        for subset2 in consequent:
                            consequent2 = consequent - frozenset([subset2])
                            rules.append({
                                'Produk A': ', '.join(list(antecedent)),
                                'Produk B': ', '.join(list([subset2])),
                                'Produk C': ', '.join(list(consequent2)),
                                'Support': support_union,
                                'Confidence': confidence,
                                'Lift': lift
                            })
    return rules

# ================================================================
# File Upload & Preprocessing
# ---------------------------------------------------------------
uploaded_file = st.file_uploader("📂 Upload File Excel (.xlsx) yang Sudah Dipreproses", type=["xlsx"])
if uploaded_file is None:
    st.info("Silakan unggah file Excel (.xlsx) yang sudah dipreproses.")
    st.stop()

# Try to read the file
try:
    df_raw = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Gagal membaca Excel: {e}")
    st.stop()

# Load transactions from the dataframe
transactions = load_transactions_from_df(df_raw)

# Show the number of transactions detected
st.write(f"Jumlah transaksi terdeteksi: **{len(transactions)}**")

if not transactions:
    st.error("Dataset tidak mengandung transaksi valid.")
    st.stop()

# ================================================================
# ECLAT Analysis
# ================================================================
st.subheader("Analisis ECLAT")
st.markdown("Menampilkan frequent itemset produk berdasarkan ECLAT.")

# Run ECLAT algorithm
frequent_itemsets = eclat(transactions, min_support)

# Filter frequent itemsets for the selected itemset size
itemsets_selected = [itemset for itemset, _ in frequent_itemsets if len(itemset) == frequent_k]

# Display frequent itemsets
st.subheader(f"Frequent {frequent_k}-Itemsets")
st.write(f"{frequent_k}-Itemsets: {len(itemsets_selected)}")

# Show frequent itemsets
if frequent_itemsets:
    itemsets_display = []
    for itemset, tidset in frequent_itemsets:
        if len(itemset) == frequent_k:
            itemsets_display.append({
                'Itemset': ', '.join(list(itemset)),
                'Support': len(tidset) / len(transactions)
            })
    
    # Convert to DataFrame for display
    frequent_itemsets_df = pd.DataFrame(itemsets_display)
    frequent_itemsets_df = frequent_itemsets_df.sort_values(by="Support", ascending=False).reset_index(drop=True)
    st.dataframe(frequent_itemsets_df.head(50), use_container_width=True)

# ================================================================
# Aturan Asosiasi
# ================================================================
st.subheader("Aturan Asosiasi")
st.markdown("Menampilkan aturan asosiasi antara produk, termasuk support, confidence, dan lift.")

# Calculate Confidence and Lift
rules = calculate_confidence_lift(frequent_itemsets, transactions)

# Display the association rules
if rules:
    rules_df = pd.DataFrame(rules)
    rules_df = rules_df.sort_values(by="Lift", ascending=False).reset_index(drop=True)
    st.dataframe(rules_df.head(30), use_container_width=True)

# ================================================================
# Top-K Bundling (Support Tertinggi)
# ================================================================
st.subheader("TOP-K Bundling (Support Tertinggi)")

# Top-K Bundling based on association rules
top_k_bundles = sorted(rules, key=lambda x: x['Support'], reverse=True)
top_k_bundles_display = top_k_bundles[:select_top_k]

top_k_df = pd.DataFrame(top_k_bundles_display)

st.dataframe(top_k_df, use_container_width=True)
