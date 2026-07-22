import pandas as pd

df = pd.read_excel('TransactionStatement.xlsx')
df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')

credits = df[df['Type'] == 'Credit'].copy()
debits = df[df['Type'] == 'Debit'].copy()

print("=== ALL CREDIT SOURCES ===")
src = credits.groupby('Transaction Details')['Amount'].agg(['sum','count']).sort_values('sum', ascending=False)
src.columns = ['Total', 'Count']
for name, row in src.iterrows():
    print(f"  Rs. {row['Total']:>10,.0f}  ({int(row['Count']):>2}x)  {name}")

print(f"\n=== CREDIT TOTAL: Rs. {credits['Amount'].sum():,.0f} ===")

# Identify self-transfers: credits FROM the account holder's own name
# ROHAN RAJ is likely the account holder
self_keywords = ['ROHAN RAJ', 'Refund Received', 'Payment Received']
self_credits = credits[credits['Transaction Details'].str.contains('|'.join(self_keywords), case=False, na=False)]
actual_income = credits[~credits['Transaction Details'].str.contains('|'.join(self_keywords), case=False, na=False)]

print(f"\n=== SELF-TRANSFERS (ROHAN RAJ + Refunds + Payment Received) ===")
print(f"Count: {len(self_credits)}, Total: Rs. {self_credits['Amount'].sum():,.0f}")
self_src = self_credits.groupby('Transaction Details')['Amount'].agg(['sum','count']).sort_values('sum', ascending=False)
for name, row in self_src.iterrows():
    print(f"  Rs. {row['sum']:>10,.0f}  ({int(row['count']):>2}x)  {name}")

print(f"\n=== ACTUAL INCOME (from others) ===")
print(f"Count: {len(actual_income)}, Total: Rs. {actual_income['Amount'].sum():,.0f}")
inc_src = actual_income.groupby('Transaction Details')['Amount'].agg(['sum','count']).sort_values('sum', ascending=False)
for name, row in inc_src.iterrows():
    print(f"  Rs. {row['sum']:>10,.0f}  ({int(row['count']):>2}x)  {name}")

print(f"\n=== DEBIT SUMMARY ===")
print(f"Total debits: Rs. {debits['Amount'].sum():,.0f} ({len(debits)} txns)")
print(f"Actual income: Rs. {actual_income['Amount'].sum():,.0f} ({len(actual_income)} txns)")
print(f"Deficit (spent - earned): Rs. {debits['Amount'].sum() - actual_income['Amount'].sum():,.0f}")
