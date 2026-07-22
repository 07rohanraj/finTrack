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
    if any(k in p for k in ['myntra', 'flipkart', 'amazon', 'meesho', 'zepto', 'zudio', 'ajio', 'nykaa']):
        return 'Shopping & E-Commerce'
    if any(k in p for k in ['google play', 'google india digital', 'youtube', 'netflix', 'kukufm', 'testbook', 'razorpay']):
        return 'Subscriptions & Digital'
    if any(k in p for k in ['shaadi ki biryani', 'biryani', 'hotel', 'restaurant', 'cafe', 'coffee', 'pizza', 'bakery', 'food', 'juice', 'tea', 'momos', 'saloon', 'salon', 'gents parlour', 'morning star', 'hungry heist', 'milo', 'pappu nishad', 'pappu nishad', 'richmond soft', 'richmond', 'soft drink', 'barber']):
        return 'Food & Dining'
    if any(k in p for k in ['mangalore fresh', 'manglore fresh', 'sagaya raj', 'nandhini', 'star bazaar', 'supermarket', 'royal mart', 'fresh', 'vegetable', 'fruit', 'coconut', 'condiment', 'groceries', 'pan shop', 'shopee', 'olive mart', 'store', 'shop', 'market']):
        return 'Groceries & Essentials'
    if any(k in p for k in ['medplus', 'medical', 'pharmacy', 'fatima', 'mamtha']):
        return 'Medical'
    if any(k in p for k in ['irctc', 'indian railways', 'train', 'flight', 'amazon flights', 'redbus']):
        return 'Travel'
    if any(k in p for k in ['bank account']):
        return 'Bank Transfer'
    if any(k in p for k in ['kalluri', 'aruna', 'purti jain', 'pbabu', 'y peda babu', 'sumanth', 'juhi', 'j uhi', 'abhishek']):
        return 'Personal Transfers'
    if any(k in p for k in ['abdul aziz', 'abdul', 'saiful', 'anish', 'srujan', 'srushty', 'rohan', 'saumik', 'indrajit']):
        return 'Personal Transfers'
    if any(k in p for k in ['soumya', 'soubhagya', 'chandan', 'vimalesh', 'harisp', 'anil', 'manjunath', 'santosh', 'ramakrishna', 'kavitha', 'umesh']):
        return 'Personal Transfers'
    if any(k in p for k in ['girdhari', 'ramchandra', 'dineshprad', 'mr.', 'sreedhar', 'alen', 'lavan', 'gautam', 'mubeen', 'amreen', 'sushil', 'murali']):
        return 'Personal Transfers'
    return 'Others'

debits['Category'] = debits['Transaction Details'].apply(categorize)

cats = debits.groupby('Category')['Amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
cats.columns = ['Total_Spent', 'Txns']
cats['Pct'] = (cats['Total_Spent'] / cats['Total_Spent'].sum() * 100).round(1)

for cat, row in cats.iterrows():
    total = row['Total_Spent']
    txns = int(row['Txns'])
    pct = row['Pct']
    bar = '#' * int(pct / 2)
    print(f"  {cat:<30} Rs.{total:>10,.0f}  ({txns:>4} txns) {pct:>5.1f}%  {bar}")

print("-" * 70)
print(f"  {'TOTAL':<30} Rs.{cats['Total_Spent'].sum():>10,.0f}  ({int(cats['Txns'].sum()):>4} txns)")

others = debits[debits['Category'] == 'Others']
print(f"\n=== OTHERS ({len(others)} txns, Rs. {others['Amount'].sum():,.0f}) ===")
top_others = others.groupby('Transaction Details')['Amount'].agg(['sum','count']).sort_values('sum', ascending=False).head(20)
for name, row in top_others.iterrows():
    print(f"  Rs. {row['sum']:>8,.0f}  ({int(row['count']):>2}x)  {name}")
