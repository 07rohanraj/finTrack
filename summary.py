import pandas as pd

df = pd.read_excel('TransactionStatement.xlsx')
df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
debits = df[df['Type'] == 'Debit'].copy()

def categorize(payee):
    p = payee.lower()
    if any(k in p for k in ['upstox', 'icici prudential', 'securities']):
        return 'Investment'
    if any(k in p for k in ['bmtc', 'bmrc', 'metro rail', 'petrol', 'diesel', 'fuel', 'krishna petroleum', 'dharamaa service']):
        return 'Transport & Fuel'
    if any(k in p for k in ['jio', 'airtel', 'prepaid recharg']):
        return 'Mobile Recharge'
    if any(k in p for k in ['myntra', 'flipkart', 'amazon', 'meesho', 'zepto', 'zudio', 'ajio']):
        return 'Shopping'
    if any(k in p for k in ['google play', 'google india digital', 'youtube', 'netflix', 'kukufm', 'testbook']):
        return 'Subscriptions & Digital'
    if any(k in p for k in ['shaadi ki biryani', 'biryani', 'hotel', 'restaurant', 'cafe', 'coffee', 'pizza', 'bakery', 'food', 'juice', 'tea', 'momos', 'saloon', 'salon', 'gents parlour']):
        return 'Food & Dining'
    if any(k in p for k in ['mangalore fresh', 'manglore fresh', 'sagaya raj', 'nandhini', 'star bazaar', 'supermarket', 'royal mart', 'fresh', 'vegetable', 'fruit', 'coconut', 'condiment', 'groceries', 'pan shop']):
        return 'Groceries & Essentials'
    if any(k in p for k in ['medplus', 'medical', 'pharmacy', 'fatima', 'mamtha']):
        return 'Medical'
    if any(k in p for k in ['irctc', 'indian railways', 'train', 'flight', 'amazon flights']):
        return 'Travel'
    if any(k in p for k in ['bank account']):
        return 'Bank Transfer'
    return 'Others'

debits['Category'] = debits['Transaction Details'].apply(categorize)

print("=" * 65)
print("CATEGORY BREAKDOWN")
print("=" * 65)
cats = debits.groupby('Category')['Amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
cats.columns = ['Total_Spent', 'Txns']
cats['Pct'] = (cats['Total_Spent'] / cats['Total_Spent'].sum() * 100).round(1)

for cat, row in cats.iterrows():
    total = row['Total_Spent']
    txns = int(row['Txns'])
    pct = row['Pct']
    bar = '#' * int(pct / 2)
    print(f"  {cat:<28} Rs.{total:>10,.0f}  ({txns:>4} txns) {pct:>5.1f}%  {bar}")

total_spend = cats['Total_Spent'].sum()
total_txns = int(cats['Txns'].sum())
print("-" * 65)
print(f"  {'TOTAL':<28} Rs.{total_spend:>10,.0f}  ({total_txns:>4} txns)")
print()

print("=" * 65)
print("KEY INSIGHTS")
print("=" * 65)
print(f"  Total spent: Rs. {total_spend:,.0f}")
print(f"  Total received: Rs. {df[df['Type']=='Credit']['Amount'].sum():,.0f}")
print(f"  Net outflow: Rs. {total_spend - df[df['Type']=='Credit']['Amount'].sum():,.0f}")
print(f"  Unique payees: {debits['Transaction Details'].nunique()}")
print(f"  Avg transaction: Rs. {debits['Amount'].mean():,.0f}")
print(f"  Median transaction: Rs. {debits['Amount'].median():,.0f}")
print(f"  Most frequent: {debits['Transaction Details'].value_counts().index[0]} ({debits['Transaction Details'].value_counts().iloc[0]} times)")
print(f"  Biggest single: Rs. {debits['Amount'].max():,.0f}")
