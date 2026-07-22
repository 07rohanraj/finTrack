import pandas as pd

df = pd.read_excel('TransactionStatement.xlsx')

# Convert date to datetime
df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
df['Month'] = df['Datetime'].dt.to_period('M')
df['Year'] = df['Datetime'].dt.year
df['Month_Name'] = df['Datetime'].dt.strftime('%b %Y')

debits = df[df['Type'] == 'Debit'].copy()
credits = df[df['Type'] == 'Credit'].copy()

print("=== SHAPE ===")
print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")

print("\n=== DATE RANGE ===")
print(f"From: {df['Date'].iloc[0]}")
print(f"To: {df['Date'].iloc[-1]}")

print(f"\n=== DEBITS: {len(debits)} txns, Total: Rs. {debits['Amount'].sum():,.2f} ===")
print(f"=== CREDITS: {len(credits)} txns, Total: Rs. {credits['Amount'].sum():,.2f} ===")

print("\n=== TOP 25 PAYEES BY TOTAL SPENT ===")
top_payees = debits.groupby('Transaction Details')['Amount'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(25)
top_payees.columns = ['Total_Spent', 'Txn_Count']
print(top_payees.to_string())

print("\n=== TOP 25 PAYEES BY TXN COUNT ===")
top_count = debits.groupby('Transaction Details')['Amount'].agg(['count', 'sum']).sort_values('count', ascending=False).head(25)
top_count.columns = ['Txn_Count', 'Total_Spent']
print(top_count.to_string())

print("\n=== MONTHLY SPENDING (top 20) ===")
monthly = debits.groupby('Month')['Amount'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(20)
monthly.columns = ['Total_Spent', 'Txn_Count']
print(monthly.to_string())

print("\n=== YEARLY SPENDING ===")
yearly = debits.groupby('Year')['Amount'].agg(['sum', 'count'])
yearly.columns = ['Total_Spent', 'Txn_Count']
print(yearly.to_string())

print("\n=== CREDIT SOURCES ===")
credit_sources = credits.groupby('Transaction Details')['Amount'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(15)
credit_sources.columns = ['Total_Received', 'Txn_Count']
print(credit_sources.to_string())

print("\n=== AMOUNT RANGE DISTRIBUTION (Debits) ===")
bins = [0, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 50000, 200000]
labels = ['0-50', '51-100', '101-200', '201-500', '501-1k', '1k-2k', '2k-5k', '5k-10k', '10k-50k', '50k+']
debits['Range'] = pd.cut(debits['Amount'], bins=bins, labels=labels)
range_dist = debits['Range'].value_counts().sort_index()
print(range_dist)

print("\n=== AMOUNT STATISTICS (Debits) ===")
print(f"Min: Rs. {debits['Amount'].min():.2f}")
print(f"Max: Rs. {debits['Amount'].max():.2f}")
print(f"Mean: Rs. {debits['Amount'].mean():.2f}")
print(f"Median: Rs. {debits['Amount'].median():.2f}")
print(f"Std Dev: Rs. {debits['Amount'].std():.2f}")

print("\n=== UNIQUE PAYEES ===")
print(f"Total unique payees: {debits['Transaction Details'].nunique()}")
