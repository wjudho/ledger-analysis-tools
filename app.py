import pandas as pd
import streamlit as st

# Set pandas display options (thousand separators)
pd.set_option('display.float_format', '{:,.0f}'.format)

# Load csv
opening_balance = pd.read_csv('opening-balance.csv')
journal_entries = pd.read_csv('bank-mandiri.csv')

# Ensure 'code' column is of type string in both DataFrames
opening_balance['code'] = opening_balance['code'].astype(str)
journal_entries['code'] = journal_entries['code'].astype(str)

journal_aggregated = journal_entries.groupby('code').agg({
    'mandiri_dr': 'sum',
    'mandiri_cr': 'sum'
}).reset_index()

# Identify the subtotal for mandiri_dr and mandiri_cr
mandiri_total_dr = journal_entries['mandiri_dr'].sum()
mandiri_total_cr = journal_entries['mandiri_cr'].sum()

# Merge with opening balances
trial_balance = pd.merge(
    opening_balance, 
    journal_aggregated, 
    on='code', 
    how='left'
).fillna(0)

# Convert 'code' to string explicitly
trial_balance['code'] = trial_balance['code'].astype(str)

# Ensure "1101105" is correctly updated with mandiri subtotals
mask = trial_balance['code'] == "1101105"
trial_balance.loc[mask, 'mandiri_dr'] += mandiri_total_cr
trial_balance.loc[mask, 'mandiri_cr'] += mandiri_total_dr

# Fill NaN values with 0 (for accounts with no transactions)
trial_balance['mandiri_dr'] = trial_balance['mandiri_dr'].fillna(0)
trial_balance['mandiri_cr'] = trial_balance['mandiri_cr'].fillna(0)

# Convert opening balances to numeric (handle commas and dashes)
trial_balance['opening_dr'] = trial_balance['opening_dr'].replace({'-': '0', ',': ''}, regex=True).astype(float)
trial_balance['opening_cr'] = trial_balance['opening_cr'].replace({'-': '0', ',': ''}, regex=True).astype(float)

# Calculate saldo akhir debit dan saldo akhit credit
trial_balance['saldo_akhir_dr'] = trial_balance['opening_dr'] + trial_balance['mandiri_dr'] - trial_balance['mandiri_cr']
trial_balance['saldo_akhir_cr'] = trial_balance['opening_cr'] + trial_balance['mandiri_cr'] - trial_balance['mandiri_dr']

# Filter our accounts with no activity (both opening and journal entries are zero)
trial_balance = trial_balance[
    (trial_balance['opening_dr'] != 0) |
    (trial_balance['opening_cr'] != 0) |
    (trial_balance['mandiri_dr'] != 0) |
    (trial_balance['mandiri_cr'] != 0)
]

# Select and reorder colums
columns_order = [
    'code',
    'name',
    'opening_dr',
    'opening_cr',
    'mandiri_dr',
    'mandiri_cr',
    'saldo_akhir_dr',
    'saldo_akhir_cr'
]
trial_balance = trial_balance[columns_order]

# Calculate subtotals for DR and CR columns
subtotal_dr = trial_balance[['opening_dr', 'mandiri_dr', 'saldo_akhir_dr']].sum().round(0)
subtotal_cr = trial_balance[['opening_cr', 'mandiri_cr', 'saldo_akhir_cr']].sum().round(0)

# Create subtotal row
subtotal_row = pd.DataFrame({
    'code': ['SUBTOTAL'],
    'name': [''],
    'opening_dr': [subtotal_dr['opening_dr']],
    'opening_cr': [subtotal_cr['opening_cr']],
    'mandiri_dr': [subtotal_dr['mandiri_dr']],
    'mandiri_cr': [subtotal_cr['mandiri_cr']],
    'saldo_akhir_dr': [subtotal_dr['saldo_akhir_dr']],
    'saldo_akhir_cr': [subtotal_cr['saldo_akhir_cr']]
})

# Append the subtotal row to the trial balance
trial_balance_with_subtotal = pd.concat([trial_balance, subtotal_row], ignore_index=True)

# Check if total DR equals total CR for each category
balance_status = []

# Check opening_dr vs opening_cr
balance_status.append({
    'category': 'Opening',
    'debit': subtotal_dr['opening_dr'],
    'credit': subtotal_cr['opening_cr'],
    'status': '✅ Balanced' if subtotal_dr['opening_dr'] == subtotal_cr['opening_cr'] else '❌ Not Balanced'
})

# Check mandiri_dr vs mandiri_cr
balance_status.append({
    'category': 'Mandiri',
    'debit': subtotal_dr['mandiri_dr'],
    'credit': subtotal_cr['mandiri_cr'],
    'status': '✅ Balanced' if subtotal_dr['mandiri_dr'] == subtotal_cr['mandiri_cr'] else '❌ Not Balanced'
})

# Check saldo_akhir_dr vs saldo_akhir_cr
balance_status.append({
    'category': 'Saldo Akhir',
    'debit': subtotal_dr['saldo_akhir_dr'],
    'credit': subtotal_cr['saldo_akhir_cr'],
    'status': '✅ Balanced' if subtotal_dr['saldo_akhir_dr'] == subtotal_cr['saldo_akhir_cr'] else '❌ Not Balanced'
})

# Convert balance status to a Dataframe
balanced_df = pd.DataFrame(balance_status)

# Display balance status in streamlit
st.title("Balance Status")
st.dataframe(balanced_df)

# Save the trial balance to CSV
trial_balance_with_subtotal.to_csv('trial_balance.csv', index=False)

# Display the trial balance in streamlit
st.title("Trial Balance Generator")
st.write("Trial balance generated successfully")
st.dataframe(trial_balance_with_subtotal)