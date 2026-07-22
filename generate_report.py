"""
Spending Analysis Report — Actual Spending Only
Excludes: Personal Transfers, Investment, Bank Transfer
Generates: PNG charts, CSV summaries, and a text report in reports/
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import seaborn as sns
import numpy as np
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')

# ── Load & prepare ───────────────────────────────────────────────
df = pd.read_excel('TransactionStatement.xlsx')
df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
df['Month'] = df['Datetime'].dt.to_period('M')
df['Year'] = df['Datetime'].dt.year
df['DayOfWeek'] = df['Datetime'].dt.day_name()
df['Quarter'] = df['Datetime'].dt.to_period('Q')

debits_all = df[df['Type'] == 'Debit'].copy()


# ── Category classifier ──────────────────────────────────────────
def categorize(payee: str) -> str:
    p = payee.lower()

    if any(k in p for k in ['upstox', 'icici prudential', 'zerodha', 'groww']):
        return 'Investment'

    if any(k in p for k in ['bmtc', 'bmrc', 'metro rail', 'bangalore metro',
                             'petrol', 'diesel', 'yash anand fuel',
                             'krishna petroleum', 'dharamaa service']):
        return 'Transport & Fuel'

    if any(k in p for k in ['jio', 'airtel', 'prepaid recharg']):
        return 'Mobile Recharge'

    if any(k in p for k in ['myntra', 'flipkart', 'amazon', 'meesho', 'zepto',
                             'zudio', 'ajio', 'nykaa', 'tata cliq', 'ekart',
                             'anuyojya', 'city enterprises', 'garment']):
        return 'Shopping & E-Commerce'

    if any(k in p for k in ['google play', 'google india digital', 'youtube',
                             'netflix', 'hotstar', 'spotify', 'kukufm',
                             'testbook', 'bookmyshow', 'razorpay']):
        return 'Subscriptions & Digital'

    if any(k in p for k in ['shaadi ki biryani', 'shaad ki', 'biryani', 'hotel',
                             'restaurant', 'cafe', 'coffee', 'pizza', 'bakery',
                             'food', 'juice', 'tea', 'momos', 'morning star',
                             'hungry heist', 'pappu nishad', 'richmond soft',
                             'soft drink', 'krishna food', 'sivam bengali',
                             'j and b kitchen', 'green theory', 'varaha cafe',
                             'tea break', 'chirus', 'ponlait', 'milon juice',
                             'divya juice', 'juice bar', 'fruit shope',
                             'bharathi fast', 'y v tea', 'quick pick coffee',
                             'kannamma fruit', 'amman fruit', 'sbm store',
                             'city store', 'sri ganga', 'sri vinayaka',
                             'sri brahmalingeswara', 'bhrama lingeshwara',
                             'sri neevi', 'y v tea shop']):
        return 'Food & Dining'

    if any(k in p for k in ['mangalore fresh', 'manglore fresh', 'sagaya raj',
                             'nandhini', 'star bazaar', 'supermarket',
                             'royal mart', 'vegetable', 'fruit', 'coconut',
                             'condiment', 'groceries', 'amazon pay groceries',
                             'pan shop', 'olive mart', 'chaithra', 'kamakshi',
                             'doddamma', 'sri durga', 'mother dairy',
                             'sri lakshmi', 'sri brahmalingeswara juice',
                             'y v tea stall', 'kamakshi vegetable']):
        return 'Groceries & Essentials'

    if any(k in p for k in ['medplus', 'medical', 'pharmacy', 'fatima',
                             'mamtha', 'sachin medical', 'sanjay medical']):
        return 'Medical & Health'

    if any(k in p for k in ['irctc', 'indian railways', 'train', 'flight',
                             'amazon flights', 'redbus', 'paytm travel',
                             'palm suites']):
        return 'Travel & Stays'

    if any(k in p for k in ['bank account']):
        return 'Bank Transfer'

    if any(k in p for k in ['bill paid', 'credit card']):
        return 'Credit Card Payment'

    if any(k in p for k in ['mithila time', 'optical', 'watch', 'salon',
                             'saloon', 'gents parlour', 'barber']):
        return 'Personal Care'

    if any(k in p for k in ['electricity', 'water bill', 'gas bill',
                             'broadband', 'wifi']):
        return 'Utilities'

    return 'Personal Transfers'


debits_all['Category'] = debits_all['Transaction Details'].apply(categorize)

# ── FILTER: Keep only actual spending ────────────────────────────
EXCLUDE = {'Personal Transfers', 'Investment', 'Bank Transfer'}
debits = debits_all[~debits_all['Category'].isin(EXCLUDE)].copy()

# ── Helpers ──────────────────────────────────────────────────────
def fmt(x, _):
    if x >= 100000:
        return f'{x/100000:.1f}L'
    if x >= 1000:
        return f'{x/1000:.0f}K'
    return f'{int(x)}'

RS = 'Rs.'

# ── 1. Main spending chart (PNG) ────────────────────────────────
print("Generating charts...")

n_txns = len(debits)
total_amt = debits['Amount'].sum()
n_payees = debits['Transaction Details'].nunique()

fig = plt.figure(figsize=(24, 40))
fig.suptitle(
    f'Actual Spending Report  |  Excluding Transfers & Investments\n'
    f'Jun 2024 - Jul 2026  |  XX6650  |  {n_txns:,} Transactions  |  {RS}{total_amt:,.0f} Total Spent',
    fontsize=18, fontweight='bold', y=0.99)

gs = gridspec.GridSpec(6, 2, hspace=0.42, wspace=0.3, top=0.96, bottom=0.02, left=0.08, right=0.95)

# --- Chart 1: Category Pie ---
ax1 = fig.add_subplot(gs[0, 0])
cat_totals = debits.groupby('Category')['Amount'].sum().sort_values(ascending=False)
colors_pie = sns.color_palette("Set2", len(cat_totals))
wedges, texts, autotexts = ax1.pie(
    cat_totals.values, labels=None, autopct='%1.1f%%',
    colors=colors_pie, pctdistance=0.78, startangle=140,
    wedgeprops={'linewidth': 1.2, 'edgecolor': 'white'}
)
for t in autotexts:
    t.set_fontsize(9)
    t.set_fontweight('bold')
ax1.legend(cat_totals.index, loc='center left', bbox_to_anchor=(-0.15, 0.5), fontsize=9, frameon=True)
ax1.set_title('Spending by Category', fontsize=14, fontweight='bold', pad=15)

# --- Chart 2: Category Horizontal Bar ---
ax2 = fig.add_subplot(gs[0, 1])
cat_bar = debits.groupby('Category')['Amount'].sum().sort_values(ascending=True)
cat_colors = sns.color_palette("Set2", len(cat_bar))
ax2.barh(range(len(cat_bar)), cat_bar.values, color=cat_colors, edgecolor='white', linewidth=0.5)
ax2.set_yticks(range(len(cat_bar)))
ax2.set_yticklabels(cat_bar.index, fontsize=10)
ax2.set_title('Total Amount by Category', fontsize=14, fontweight='bold')
ax2.set_xlabel('Amount (Rs.)')
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for i, v in enumerate(cat_bar.values):
    ax2.text(v + 200, i, f'{RS}{v:,.0f}', va='center', fontsize=9)

# --- Chart 3: Top 20 Payees by Amount ---
ax3 = fig.add_subplot(gs[1, 0])
top20 = debits.groupby('Transaction Details')['Amount'].sum().sort_values(ascending=True).tail(20)
clean_names = [n.replace('Paid to ', '').replace('Paid ', '(no name)')[:35] for n in top20.index]
colors3 = plt.cm.Reds(np.linspace(0.25, 0.85, 20))
ax3.barh(range(len(top20)), top20.values, color=colors3)
ax3.set_yticks(range(len(top20)))
ax3.set_yticklabels(clean_names, fontsize=8)
ax3.set_title('Top 20 Payees by Total Spent', fontsize=14, fontweight='bold')
ax3.set_xlabel('Amount (Rs.)')
ax3.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for i, v in enumerate(top20.values):
    ax3.text(v + 100, i, f'{RS}{v:,.0f}', va='center', fontsize=7.5)

# --- Chart 4: Top 20 Payees by Count ---
ax4 = fig.add_subplot(gs[1, 1])
top20c = debits.groupby('Transaction Details')['Amount'].agg(['count', 'sum']).sort_values('count', ascending=True).tail(20)
clean_names_c = [n.replace('Paid to ', '').replace('Paid ', '(no name)')[:35] for n in top20c.index]
colors4 = plt.cm.Blues(np.linspace(0.25, 0.85, 20))
ax4.barh(range(len(top20c)), top20c['count'], color=colors4)
ax4.set_yticks(range(len(top20c)))
ax4.set_yticklabels(clean_names_c, fontsize=8)
ax4.set_title('Top 20 Payees by Transaction Count', fontsize=14, fontweight='bold')
ax4.set_xlabel('Number of Transactions')
for i, v in enumerate(top20c['count'].values):
    ax4.text(v + 0.3, i, str(v), va='center', fontsize=8)

# --- Chart 5: Monthly Spending Trend (full width) ---
ax5 = fig.add_subplot(gs[2, :])
monthly = debits.groupby('Month')['Amount'].sum()
monthly.index = monthly.index.to_timestamp()
ax5.fill_between(monthly.index, monthly.values, alpha=0.2, color='steelblue')
ax5.plot(monthly.index, monthly.values, color='steelblue', linewidth=2, marker='o', markersize=4)
avg_line = monthly.mean()
ax5.axhline(y=avg_line, color='red', linestyle='--', linewidth=1, alpha=0.7,
            label=f'Monthly Avg: {RS}{avg_line:,.0f}')
ax5.set_title('Monthly Actual Spending Trend', fontsize=14, fontweight='bold')
ax5.set_ylabel('Amount (Rs.)')
ax5.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax5.tick_params(axis='x', rotation=45)
ax5.legend(fontsize=10, loc='upper left')
peak_m, peak_v = monthly.idxmax(), monthly.max()
ax5.annotate(f'Peak: {RS}{peak_v:,.0f}\n({peak_m.strftime("%b %Y")})',
             xy=(peak_m, peak_v), xytext=(peak_m, peak_v * 1.2),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=9, color='red', ha='center', fontweight='bold')
trough_m, trough_v = monthly.idxmin(), monthly.min()
ax5.annotate(f'Low: {RS}{trough_v:,.0f}\n({trough_m.strftime("%b %Y")})',
             xy=(trough_m, trough_v), xytext=(trough_m, trough_v + avg_line * 0.5),
             arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
             fontsize=9, color='green', ha='center')

# --- Chart 6: Quarterly Spending ---
ax6 = fig.add_subplot(gs[3, 0])
quarterly = debits.groupby('Quarter')['Amount'].sum()
quarterly.index = quarterly.index.to_timestamp()
q_colors = sns.color_palette("viridis", len(quarterly))
bars = ax6.bar(quarterly.index, quarterly.values, width=70, color=q_colors, edgecolor='white')
ax6.set_title('Quarterly Spending', fontsize=14, fontweight='bold')
ax6.set_ylabel('Amount (Rs.)')
ax6.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax6.tick_params(axis='x', rotation=45)
for bar, val in zip(bars, quarterly.values):
    ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
             f'{RS}{val/1000:.1f}K', ha='center', fontsize=8, fontweight='bold')

# --- Chart 7: Yearly Comparison ---
ax7 = fig.add_subplot(gs[3, 1])
yearly = debits.groupby('Year')['Amount'].sum()
yearly_count = debits.groupby('Year').size()
y_colors = ['#e74c3c', '#3498db', '#2ecc71']
bars = ax7.bar(yearly.index.astype(str), yearly.values, color=y_colors[:len(yearly)], width=0.5, edgecolor='white')
ax7.set_title('Yearly Spending', fontsize=14, fontweight='bold')
ax7.set_ylabel('Amount (Rs.)')
ax7.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for bar, val, cnt in zip(bars, yearly.values, yearly_count.values):
    ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
             f'{RS}{val:,.0f}\n({cnt} txns)', ha='center', fontsize=10, fontweight='bold')

# --- Chart 8: Amount Distribution (histogram) ---
ax8 = fig.add_subplot(gs[4, 0])
small_txns = debits[debits['Amount'] <= 1000]['Amount']
ax8.hist(small_txns, bins=50, color='coral', edgecolor='white', alpha=0.8)
med_val = debits['Amount'].median()
mean_val = debits['Amount'].mean()
ax8.axvline(x=med_val, color='navy', linestyle='--', linewidth=1.5, label=f'Median: {RS}{med_val:.0f}')
ax8.axvline(x=mean_val, color='darkgreen', linestyle=':', linewidth=1.5, label=f'Mean: {RS}{mean_val:,.0f}')
ax8.set_title('Transaction Amount Distribution (<= Rs. 1,000)', fontsize=14, fontweight='bold')
ax8.set_xlabel('Amount (Rs.)')
ax8.set_ylabel('Frequency')
ax8.legend(fontsize=9)

# --- Chart 9: Day of Week spending ---
ax9 = fig.add_subplot(gs[4, 1])
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow = debits.groupby('DayOfWeek')['Amount'].agg(['sum', 'count']).reindex(dow_order)
dow_avg = dow['sum'] / dow['count']
x_pos = range(len(dow))
bars = ax9.bar(x_pos, dow_avg.values, color=sns.color_palette("coolwarm", 7), width=0.6, edgecolor='white')
ax9.set_xticks(list(x_pos))
ax9.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], fontsize=9)
ax9.set_title('Avg Transaction Size by Day of Week', fontsize=14, fontweight='bold')
ax9.set_ylabel('Avg Amount (Rs.)')
ax9.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
for bar, val in zip(bars, dow_avg.values):
    ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
             f'{RS}{val:.0f}', ha='center', fontsize=9, fontweight='bold')

# --- Chart 10: Category avg transaction size ---
ax10 = fig.add_subplot(gs[5, 0])
cat_stats = debits.groupby('Category')['Amount'].agg(['mean', 'median']).sort_values('mean', ascending=True)
x = range(len(cat_stats))
w = 0.35
ax10.barh([i - w/2 for i in x], cat_stats['mean'], w, label='Mean', color='steelblue', alpha=0.8)
ax10.barh([i + w/2 for i in x], cat_stats['median'], w, label='Median', color='coral', alpha=0.8)
ax10.set_yticks(list(x))
ax10.set_yticklabels(cat_stats.index, fontsize=9)
ax10.set_title('Avg Transaction Size by Category', fontsize=14, fontweight='bold')
ax10.set_xlabel('Amount (Rs.)')
ax10.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax10.legend(fontsize=9)

# --- Chart 11: Cumulative spending ---
ax11 = fig.add_subplot(gs[5, 1])
deb_sorted = debits.sort_values('Datetime')
cumulative = deb_sorted['Amount'].cumsum()
dates = deb_sorted['Datetime'].values
ax11.plot(dates, cumulative.values, color='darkorange', linewidth=2)
ax11.fill_between(dates, cumulative.values, alpha=0.15, color='orange')
ax11.set_title('Cumulative Spending Over Time', fontsize=14, fontweight='bold')
ax11.set_ylabel('Cumulative Amount (Rs.)')
ax11.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax11.tick_params(axis='x', rotation=45)
final = cumulative.values[-1]
ax11.annotate(f'Total: {RS}{final:,.0f}', xy=(dates[-1], final),
              xytext=(dates[-1], final * 0.8),
              arrowprops=dict(arrowstyle='->', color='darkorange', lw=1.5),
              fontsize=11, color='darkorange', fontweight='bold')

chart_path = REPORTS_DIR / "spending_actual.png"
plt.savefig(str(chart_path), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"  [OK] Charts saved: {chart_path}")


# ── 2. CSV Summaries ────────────────────────────────────────────
print("Generating CSV summaries...")

cat_summary = debits.groupby('Category').agg(
    Total_Spent=('Amount', 'sum'),
    Transaction_Count=('Amount', 'count'),
    Avg_Transaction=('Amount', 'mean'),
    Median_Transaction=('Amount', 'median'),
    Max_Transaction=('Amount', 'max'),
    Min_Transaction=('Amount', 'min')
).sort_values('Total_Spent', ascending=False)
cat_summary['Pct_of_Total'] = (cat_summary['Total_Spent'] / cat_summary['Total_Spent'].sum() * 100).round(1)
cat_summary.to_csv(str(REPORTS_DIR / "actual_category_summary.csv"))
print(f"  [OK] actual_category_summary.csv")

monthly_summary = debits.groupby('Month').agg(
    Total_Spent=('Amount', 'sum'),
    Transaction_Count=('Amount', 'count'),
    Avg_Transaction=('Amount', 'mean'),
    Unique_Payees=('Transaction Details', 'nunique')
).sort_index()
monthly_summary.index = monthly_summary.index.astype(str)
monthly_summary.to_csv(str(REPORTS_DIR / "actual_monthly_summary.csv"))
print(f"  [OK] actual_monthly_summary.csv")

top_payees = debits.groupby('Transaction Details').agg(
    Total_Spent=('Amount', 'sum'),
    Transaction_Count=('Amount', 'count'),
    Avg_Transaction=('Amount', 'mean'),
    Category=('Category', 'first'),
    First_Seen=('Datetime', 'min'),
    Last_Seen=('Datetime', 'max')
).sort_values('Total_Spent', ascending=False)
top_payees['First_Seen'] = top_payees['First_Seen'].dt.strftime('%Y-%m-%d')
top_payees['Last_Seen'] = top_payees['Last_Seen'].dt.strftime('%Y-%m-%d')
top_payees.to_csv(str(REPORTS_DIR / "actual_top_payees.csv"))
print(f"  [OK] actual_top_payees.csv")

quarterly_summary = debits.groupby('Quarter').agg(
    Total_Spent=('Amount', 'sum'),
    Transaction_Count=('Amount', 'count'),
    Avg_Transaction=('Amount', 'mean'),
    Unique_Payees=('Transaction Details', 'nunique')
).sort_index()
quarterly_summary.index = quarterly_summary.index.astype(str)
quarterly_summary.to_csv(str(REPORTS_DIR / "actual_quarterly_summary.csv"))
print(f"  [OK] actual_quarterly_summary.csv")

dow_summary = debits.groupby('DayOfWeek').agg(
    Total_Spent=('Amount', 'sum'),
    Transaction_Count=('Amount', 'count'),
    Avg_Transaction=('Amount', 'mean')
).reindex(dow_order)
dow_summary.to_csv(str(REPORTS_DIR / "actual_day_of_week_summary.csv"))
print(f"  [OK] actual_day_of_week_summary.csv")

debits_export = debits[['Date', 'Time', 'Transaction Details', 'Transaction ID',
                         'UTR No', 'Type', 'Amount', 'Category', 'Year', 'Month']].copy()
debits_export['Month'] = debits_export['Month'].astype(str)
debits_export.to_csv(str(REPORTS_DIR / "actual_all_debits.csv"), index=False)
print(f"  [OK] actual_all_debits.csv")


# ── 3. Text Report ──────────────────────────────────────────────
print("Generating text report...")

total_spent = debits['Amount'].sum()
total_txns = len(debits)
unique_payees = debits['Transaction Details'].nunique()
avg_txn = debits['Amount'].mean()
median_txn = debits['Amount'].median()
max_txn = debits['Amount'].max()
max_payee = debits.groupby('Transaction Details')['Amount'].sum().idxmax()
max_payee_amt = debits.groupby('Transaction Details')['Amount'].sum().max()
most_freq = debits['Transaction Details'].value_counts().index[0]
most_freq_cnt = debits['Transaction Details'].value_counts().iloc[0]
peak_month = monthly.idxmax()
peak_month_val = monthly.max()

top_cat = cat_totals.index[0]
top_cat_val = cat_totals.values[0]
top_cat_pct = (top_cat_val / total_spent * 100)

top5_cats = cat_totals.head(5)

daily = debits.groupby(debits['Datetime'].dt.date)['Amount'].sum()
daily_avg = daily.mean()
daily_max = daily.max()
daily_max_date = daily.idxmax()

# Monthly avg per category
cat_monthly_avg = debits.groupby(['Category', 'Month'])['Amount'].sum().groupby('Category').mean().sort_values(ascending=False)

report_lines = []
report_lines.append("=" * 72)
report_lines.append("           ACTUAL SPENDING REPORT — EXCLUDING TRANSFERS & INVESTMENTS")
report_lines.append("           PhonePe Statement: Jun 2024 — Jul 2026")
report_lines.append("           Account: XX6650")
report_lines.append("=" * 72)
report_lines.append("")
report_lines.append("EXCLUDED FROM THIS REPORT")
report_lines.append("-" * 72)
excl_total = debits_all[debits_all['Category'].isin(EXCLUDE)]['Amount'].sum()
excl_txns = len(debits_all[debits_all['Category'].isin(EXCLUDE)])
report_lines.append(f"  Personal Transfers:   Rs. {debits_all[debits_all['Category']=='Personal Transfers']['Amount'].sum():>10,.0f}  ({len(debits_all[debits_all['Category']=='Personal Transfers'])} txns)")
report_lines.append(f"  Investment:           Rs. {debits_all[debits_all['Category']=='Investment']['Amount'].sum():>10,.0f}  ({len(debits_all[debits_all['Category']=='Investment'])} txns)")
report_lines.append(f"  Bank Transfer:        Rs. {debits_all[debits_all['Category']=='Bank Transfer']['Amount'].sum():>10,.0f}  ({len(debits_all[debits_all['Category']=='Bank Transfer'])} txns)")
report_lines.append(f"  TOTAL EXCLUDED:       Rs. {excl_total:>10,.0f}  ({excl_txns} txns)")
report_lines.append("")
report_lines.append("EXECUTIVE SUMMARY")
report_lines.append("-" * 72)
report_lines.append(f"  Actual Money Spent:         Rs. {total_spent:>12,.2f}")
report_lines.append(f"  Total Transactions:         {total_txns:>13}")
report_lines.append(f"  Unique Payees:              {unique_payees:>13}")
report_lines.append(f"  Avg Transaction:            Rs. {avg_txn:>12,.2f}")
report_lines.append(f"  Median Transaction:         Rs. {median_txn:>12,.2f}")
report_lines.append(f"  Largest Transaction:        Rs. {max_txn:>12,.2f}")
report_lines.append(f"  Avg Daily Spending:         Rs. {daily_avg:>12,.2f}")
report_lines.append(f"  Avg Monthly Spending:       Rs. {monthly.mean():>12,.2f}")
report_lines.append(f"  Highest Single Day:         Rs. {daily_max:>12,.2f} ({daily_max_date})")
report_lines.append("")
report_lines.append("WHERE YOUR MONEY GOES")
report_lines.append("-" * 72)
report_lines.append(f"  {'Category':<32} {'Spent':>12}  {'Txns':>6}  {'Avg':>10}  {'%':>6}")
report_lines.append(f"  {'':<32} {'':>12}  {'':>6}  {'':>10}  {'':>6}")
for cat, row in cat_summary.iterrows():
    report_lines.append(f"  {cat:<32} Rs.{row['Total_Spent']:>9,.0f}  {int(row['Transaction_Count']):>6}  Rs.{row['Avg_Transaction']:>8,.0f}  {row['Pct_of_Total']:>5.1f}%")
report_lines.append(f"  {'':<32} {'':>12}  {'':>6}  {'':>10}  {'':>6}")
report_lines.append(f"  {'TOTAL ACTUAL SPENDING':<32} Rs.{total_spent:>9,.0f}  {total_txns:>6}  Rs.{avg_txn:>8,.0f}")
report_lines.append("")
report_lines.append("TOP 10 PAYEES BY AMOUNT")
report_lines.append("-" * 72)
top10_payees = debits.groupby(['Transaction Details', 'Category'])['Amount'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(10)
for (name, cat), row in top10_payees.iterrows():
    short = name.replace('Paid to ', '').replace('Paid ', '(no name)')[:35]
    report_lines.append(f"  Rs.{row['sum']:>10,.0f}  ({int(row['count']):>3}x)  {short:<35} [{cat}]")
report_lines.append("")
report_lines.append("TOP 10 MOST FREQUENT PAYEES")
report_lines.append("-" * 72)
top10_freq = debits['Transaction Details'].value_counts().head(10)
for name, cnt in top10_freq.items():
    total = debits[debits['Transaction Details'] == name]['Amount'].sum()
    cat = debits[debits['Transaction Details'] == name]['Category'].iloc[0]
    short = name.replace('Paid to ', '').replace('Paid ', '(no name)')[:35]
    report_lines.append(f"  {cnt:>4}x  Rs.{total:>10,.0f}  {short:<35} [{cat}]")
report_lines.append("")
report_lines.append("MONTHLY SPENDING BREAKDOWN")
report_lines.append("-" * 72)
report_lines.append(f"  {'Month':<12} {'Spent':>12}  {'Txns':>6}  {'Avg/Txn':>10}  {'Payees':>8}")
for month, row in monthly_summary.iterrows():
    report_lines.append(f"  {month:<12} Rs.{row['Total_Spent']:>9,.0f}  {int(row['Transaction_Count']):>6}  Rs.{row['Avg_Transaction']:>8,.0f}  {int(row['Unique_Payees']):>8}")
report_lines.append("")
report_lines.append("MONTHLY AVERAGE BY CATEGORY")
report_lines.append("-" * 72)
for cat, val in cat_monthly_avg.items():
    report_lines.append(f"  {cat:<32} Rs.{val:>9,.0f}/month")
report_lines.append("")
report_lines.append("KEY INSIGHTS")
report_lines.append("-" * 72)
report_lines.append(f"  1. Highest spending: {top_cat} — {RS}{top_cat_val:,.0f} ({top_cat_pct:.1f}% of actual spend)")
report_lines.append(f"  2. Peak spending month: {peak_month.strftime('%b %Y')} — {RS}{peak_month_val:,.0f}")
report_lines.append(f"  3. Biggest payee: {max_payee.replace('Paid to ', '')[:35]} — {RS}{max_payee_amt:,.0f}")
report_lines.append(f"  4. Most frequent: {most_freq.replace('Paid to ', '')[:35]} — {most_freq_cnt} times")
report_lines.append(f"  5. Daily avg: {RS}{daily_avg:,.0f}  |  Monthly avg: {RS}{monthly.mean():,.0f}")
report_lines.append(f"  6. Median txn: {RS}{median_txn:.0f} — most transactions are small daily payments")
report_lines.append(f"  7. Top 3 categories make up {cat_totals.head(3).sum()/total_spent*100:.0f}% of all spending")
report_lines.append("")
report_lines.append("=" * 72)
report_lines.append("  Report generated from TransactionStatement.md")
report_lines.append("  Data period: Jun 01, 2024 — Jul 21, 2026")
report_lines.append("=" * 72)

report_text = "\n".join(report_lines)
report_path = REPORTS_DIR / "spending_actual.txt"
with open(str(report_path), "w", encoding="utf-8") as f:
    f.write(report_text)
print(f"  [OK] spending_actual.txt")

print("\n" + report_text)
print(f"\nAll reports saved to: {REPORTS_DIR}")
