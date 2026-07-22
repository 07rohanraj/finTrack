import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
from pathlib import Path

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

df = pd.read_excel('TransactionStatement.xlsx')
df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
df['Month'] = df['Datetime'].dt.to_period('M')
df['Year'] = df['Datetime'].dt.year

debits = df[df['Type'] == 'Debit'].copy()
credits = df[df['Type'] == 'Credit'].copy()


def categorize(payee: str) -> str:
    p = payee.lower()

    if any(k in p for k in ['upstox', 'icici prudential', 'zerodha', 'groww']):
        return 'Investment'
    if any(k in p for k in ['bmtc', 'bmrc', 'metro rail', 'bangalore metro', 'petrol', 'diesel',
                             'yash anand fuel', 'krishna petroleum', 'dharamaa service']):
        return 'Transport & Fuel'
    if any(k in p for k in ['jio', 'airtel', 'prepaid recharg']):
        return 'Mobile Recharge'
    if any(k in p for k in ['myntra', 'flipkart', 'amazon', 'meesho', 'zepto', 'zudio',
                             'ajio', 'nykaa', 'tata cliq', 'ekart']):
        return 'Shopping & E-Commerce'
    if any(k in p for k in ['google play', 'google india digital', 'youtube', 'netflix',
                             'hotstar', 'spotify', 'kukufm', 'testbook', 'bookmyshow',
                             'razorpay', 'google play']):
        return 'Subscriptions & Digital'
    if any(k in p for k in ['shaadi ki biryani', 'shaad ki', 'biryani', 'hotel', 'restaurant',
                             'cafe', 'coffee', 'pizza', 'bakery', 'food', 'juice', 'tea',
                             'momos', 'saloon', 'salon', 'gents parlour', 'morning star',
                             'hungry heist', 'pappu nishad', 'richmond soft', 'soft drink',
                             'barber', 'krishna food', 'sivam bengali', 'j and b kitchen',
                             'green theory', 'varaha cafe', 'tea break', 'chirus', 'ponlait',
                             'milon juice', 'divya juice', 'juice bar', 'fruit shope',
                             'bharathi fast', 'y v tea', 'quick pick coffee', 'kannamma fruit',
                             'amman fruit', 'sbm store', 'city store', 'sri ganga',
                             'manglore fresh', 'sri vinayaka']):
        return 'Food & Dining & Personal Care'
    if any(k in p for k in ['mangalore fresh', 'manglore fresh', 'sagaya raj', 'nandhini',
                             'star bazaar', 'supermarket', 'royal mart', 'vegetable',
                             'fruit', 'coconut', 'condiment', 'groceries', 'amazon pay groceries',
                             'pan shop', 'shopee', 'olive mart', 'chaithra', 'kamakshi',
                             'doddamma', 'sri durga', 'nandhini', 'mother dairy',
                             'sri lakshmi']):
        return 'Groceries & Essentials'
    if any(k in p for k in ['medplus', 'medical', 'pharmacy', 'fatima', 'mamtha',
                             'sachin medical', 'sanjay medical']):
        return 'Medical & Health'
    if any(k in p for k in ['irctc', 'indian railways', 'train', 'flight', 'amazon flights',
                             'redbus', 'paytm travel', 'palm suites']):
        return 'Travel & Stays'
    if any(k in p for k in ['bank account']):
        return 'Bank Transfer'
    if any(k in p for k in ['bill paid', 'credit card']):
        return 'Credit Card Payment'
    if any(k in p for k in ['clothing', 'garment', 'anuyojya']):
        return 'Shopping & E-Commerce'
    if any(k in p for k in ['mithila time', 'optical', 'watch']):
        return 'Personal Care'

    return 'Personal Transfers'


debits['Category'] = debits['Transaction Details'].apply(categorize)


def fmt(x, _):
    if x >= 100000:
        return f'{x/100000:.1f}L'
    if x >= 1000:
        return f'{x/1000:.0f}K'
    return f'{int(x)}'


fig = plt.figure(figsize=(24, 36))
fig.suptitle('PhonePe Transaction Analysis  |  Jun 2024 \u2013 Jul 2026\nAccount: XX6650  |  2,051 Transactions  |  721 Unique Payees',
             fontsize=20, fontweight='bold', y=0.98)

gs = fig.add_gridspec(6, 2, hspace=0.4, wspace=0.3, top=0.94, bottom=0.02, left=0.08, right=0.95)


# --- 1: Top 15 Payees by Total Amount ---
ax1 = fig.add_subplot(gs[0, 0])
top15_amount = debits.groupby('Transaction Details')['Amount'].sum().sort_values(ascending=True).tail(15)
colors1 = plt.cm.Reds(np.linspace(0.3, 0.9, 15))
ax1.barh(range(len(top15_amount)), top15_amount.values, color=colors1)
ax1.set_yticks(range(len(top15_amount)))
ax1.set_yticklabels(top15_amount.index, fontsize=8)
ax1.set_title('Top 15 Payees by Total Amount Spent', fontsize=13, fontweight='bold')
ax1.set_xlabel('Amount (Rs.)')
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for i, v in enumerate(top15_amount.values):
    ax1.text(v + 1500, i, f'\u20b9{v:,.0f}', va='center', fontsize=7.5)


# --- 2: Top 15 Payees by Transaction Count ---
ax2 = fig.add_subplot(gs[0, 1])
top15_count = debits.groupby('Transaction Details')['Amount'].agg(['count', 'sum']).sort_values('count', ascending=True).tail(15)
colors2 = plt.cm.Blues(np.linspace(0.3, 0.9, 15))
ax2.barh(range(len(top15_count)), top15_count['count'], color=colors2)
ax2.set_yticks(range(len(top15_count)))
ax2.set_yticklabels(top15_count.index, fontsize=8)
ax2.set_title('Top 15 Payees by Frequency', fontsize=13, fontweight='bold')
ax2.set_xlabel('Number of Transactions')
for i, v in enumerate(top15_count['count'].values):
    ax2.text(v + 1, i, str(v), va='center', fontsize=8)


# --- 3: Spending by Category (Pie) ---
ax3 = fig.add_subplot(gs[1, 0])
cat_totals = debits.groupby('Category')['Amount'].sum().sort_values(ascending=False)
colors_pie = sns.color_palette("Set2", len(cat_totals))
wedges, texts, autotexts = ax3.pie(
    cat_totals.values, labels=cat_totals.index, autopct='%1.1f%%',
    colors=colors_pie, pctdistance=0.8, startangle=140,
    textprops={'fontsize': 9}, wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
)
for t in autotexts:
    t.set_fontsize(7.5)
    t.set_fontweight('bold')
ax3.set_title('Spending Distribution by Category', fontsize=13, fontweight='bold')


# --- 4: Category-wise Total Bar ---
ax4 = fig.add_subplot(gs[1, 1])
cat_bar = debits.groupby('Category')['Amount'].sum().sort_values(ascending=True)
cat_colors = sns.color_palette("Set2", len(cat_bar))
ax4.barh(range(len(cat_bar)), cat_bar.values, color=cat_colors)
ax4.set_yticks(range(len(cat_bar)))
ax4.set_yticklabels(cat_bar.index, fontsize=9)
ax4.set_title('Total Amount by Category', fontsize=13, fontweight='bold')
ax4.set_xlabel('Amount (Rs.)')
ax4.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for i, v in enumerate(cat_bar.values):
    ax4.text(v + 1000, i, f'\u20b9{v:,.0f}', va='center', fontsize=8)


# --- 5: Monthly Spending Trend (full width) ---
ax5 = fig.add_subplot(gs[2, :])
monthly = debits.groupby('Month')['Amount'].sum()
monthly.index = monthly.index.to_timestamp()
ax5.fill_between(monthly.index, monthly.values, alpha=0.25, color='steelblue')
ax5.plot(monthly.index, monthly.values, color='steelblue', linewidth=2, marker='o', markersize=3)
ax5.set_title('Monthly Spending Trend', fontsize=13, fontweight='bold')
ax5.set_ylabel('Amount (Rs.)')
ax5.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax5.tick_params(axis='x', rotation=45)

avg = monthly.mean()
ax5.axhline(y=avg, color='red', linestyle='--', linewidth=1, alpha=0.7, label=f'Monthly Avg: \u20b9{avg:,.0f}')
ax5.legend(fontsize=10, loc='upper left')

peak_month = monthly.idxmax()
peak_val = monthly.max()
ax5.annotate(f'Peak: \u20b9{peak_val:,.0f}\n({peak_month.strftime("%b %Y")})',
             xy=(peak_month, peak_val), xytext=(peak_month, peak_val * 1.15),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=9, color='red', ha='center', fontweight='bold')

trough_month = monthly.idxmin()
trough_val = monthly.min()
ax5.annotate(f'Low: \u20b9{trough_val:,.0f}\n({trough_month.strftime("%b %Y")})',
             xy=(trough_month, trough_val), xytext=(trough_month, trough_val + avg * 0.5),
             arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
             fontsize=9, color='green', ha='center')


# --- 6: Yearly Spending Bar ---
ax6 = fig.add_subplot(gs[3, 0])
yearly = debits.groupby('Year')['Amount'].sum()
yearly_count = debits.groupby('Year').size()
colors_yr = sns.color_palette("viridis", len(yearly))
bars = ax6.bar(yearly.index.astype(str), yearly.values, color=colors_yr, width=0.5, edgecolor='white')
ax6.set_title('Yearly Spending Comparison', fontsize=13, fontweight='bold')
ax6.set_ylabel('Amount (Rs.)')
ax6.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for bar, val, cnt in zip(bars, yearly.values, yearly_count.values):
    ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5000,
             f'\u20b9{val:,.0f}\n({cnt} txns)', ha='center', fontsize=9, fontweight='bold')


# --- 7: Debit vs Credit Summary ---
ax7 = fig.add_subplot(gs[3, 1])
total_debit = debits['Amount'].sum()
total_credit = credits['Amount'].sum()
net = total_credit - total_debit
summary_vals = [total_debit, total_credit, net]
summary_labels = ['Spent\n(Debit)', 'Received\n(Credit)', 'Net\n(Credit-Debit)']
colors_summary = ['#e74c3c', '#2ecc71', '#3498db']
bars = ax7.bar(summary_labels, summary_vals, color=colors_summary, width=0.5, edgecolor='white')
ax7.set_title('Overall Cash Flow', fontsize=13, fontweight='bold')
ax7.set_ylabel('Amount (Rs.)')
ax7.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for bar, val in zip(bars, summary_vals):
    y_pos = max(bar.get_height(), 0) + 5000
    ax7.text(bar.get_x() + bar.get_width()/2, y_pos,
             f'\u20b9{val:,.0f}', ha='center', fontsize=10, fontweight='bold')


# --- 8: Amount Distribution Histogram ---
ax8 = fig.add_subplot(gs[4, 0])
small_txns = debits[debits['Amount'] <= 1000]['Amount']
ax8.hist(small_txns, bins=50, color='coral', edgecolor='white', alpha=0.8)
median_val = debits['Amount'].median()
mean_val = debits['Amount'].mean()
ax8.axvline(x=median_val, color='navy', linestyle='--', linewidth=1.5, label=f'Median: \u20b9{median_val:.0f}')
ax8.axvline(x=mean_val, color='darkgreen', linestyle=':', linewidth=1.5, label=f'Mean: \u20b9{mean_val:,.0f}')
ax8.set_title('Transaction Amount Distribution (\u2264 \u20b91,000)', fontsize=13, fontweight='bold')
ax8.set_xlabel('Amount (Rs.)')
ax8.set_ylabel('Frequency')
ax8.legend(fontsize=9)


# --- 9: Monthly Transaction Count ---
ax9 = fig.add_subplot(gs[4, 1])
monthly_count = debits.groupby('Month').size()
monthly_count.index = monthly_count.index.to_timestamp()
ax9.bar(monthly_count.index, monthly_count.values, width=25, color='mediumpurple', alpha=0.7)
ax9.set_title('Monthly Transaction Count', fontsize=13, fontweight='bold')
ax9.set_xlabel('Month')
ax9.set_ylabel('Number of Transactions')
ax9.tick_params(axis='x', rotation=45)
avg_count = monthly_count.mean()
ax9.axhline(y=avg_count, color='red', linestyle='--', linewidth=1, alpha=0.7,
            label=f'Average: {avg_count:.0f} txns/month')
ax9.legend(fontsize=9)


# --- 10: Category-wise Avg Transaction Size ---
ax10 = fig.add_subplot(gs[5, 0])
cat_avg = debits.groupby('Category')['Amount'].agg(['mean', 'median']).sort_values('mean', ascending=True)
x = range(len(cat_avg))
width = 0.35
ax10.barh([i - width/2 for i in x], cat_avg['mean'], width, label='Mean', color='steelblue', alpha=0.8)
ax10.barh([i + width/2 for i in x], cat_avg['median'], width, label='Median', color='coral', alpha=0.8)
ax10.set_yticks(list(x))
ax10.set_yticklabels(cat_avg.index, fontsize=8)
ax10.set_title('Avg Transaction Size by Category', fontsize=13, fontweight='bold')
ax10.set_xlabel('Amount (Rs.)')
ax10.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax10.legend(fontsize=9)


# --- 11: Top 10 Credit Sources ---
ax11 = fig.add_subplot(gs[5, 1])
credit_src = credits.groupby('Transaction Details')['Amount'].sum().sort_values(ascending=True).tail(10)
colors11 = plt.cm.Greens(np.linspace(0.3, 0.9, 10))
ax11.barh(range(len(credit_src)), credit_src.values, color=colors11)
ax11.set_yticks(range(len(credit_src)))
ax11.set_yticklabels(credit_src.index, fontsize=8)
ax11.set_title('Top 10 Credit Sources', fontsize=13, fontweight='bold')
ax11.set_xlabel('Amount Received (Rs.)')
ax11.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for i, v in enumerate(credit_src.values):
    ax11.text(v + 500, i, f'\u20b9{v:,.0f}', va='center', fontsize=7.5)


output_path = Path(__file__).parent / 'spending_analysis.png'
plt.savefig(str(output_path), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {output_path}")

print("\n=== CATEGORY SUMMARY ===")
cats = debits.groupby('Category')['Amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
cats.columns = ['Total_Spent', 'Txns']
cats['Pct'] = (cats['Total_Spent'] / cats['Total_Spent'].sum() * 100).round(1)
for cat, row in cats.iterrows():
    bar = '#' * int(row['Pct'] / 2)
    print(f"  {cat:<32} Rs.{row['Total_Spent']:>10,.0f}  ({int(row['Txns']):>4} txns) {row['Pct']:>5.1f}%  {bar}")
print("-" * 75)
print(f"  {'TOTAL':<32} Rs.{cats['Total_Spent'].sum():>10,.0f}  ({int(cats['Txns'].sum()):>4} txns)")
