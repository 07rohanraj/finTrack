"""
Extra Insights Report — Second layer of analysis
New angles: heatmap, category trends, scatter, weekend/weekday, growth, diversity
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import seaborn as sns
import numpy as np
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid')

# ── Load & prepare (same as generate_report.py) ─────────────────
df = pd.read_excel('TransactionStatement.xlsx')
df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
df['Month'] = df['Datetime'].dt.to_period('M')
df['Year'] = df['Datetime'].dt.year
df['DayOfWeek'] = df['Datetime'].dt.day_name()
df['Quarter'] = df['Datetime'].dt.to_period('Q')
df['IsWeekend'] = df['Datetime'].dt.dayofweek >= 5
df['HourOfDay'] = pd.to_datetime(df['Time'], format='%I:%M %p').dt.hour

debits_all = df[df['Type'] == 'Debit'].copy()

EXCLUDE = {'Personal Transfers', 'Investment', 'Bank Transfer'}

def categorize(payee):
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
debits = debits_all[~debits_all['Category'].isin(EXCLUDE)].copy()

def fmt(x, _):
    if x >= 100000: return f'{x/100000:.1f}L'
    if x >= 1000: return f'{x/1000:.0f}K'
    return f'{int(x)}'

RS = 'Rs.'
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

print("=" * 60)
print("Generating extra insights...")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════════
# FIGURE 1: Heatmap — Day of Week × Month
# ═══════════════════════════════════════════════════════════════════
print("\n[1/3] Day-of-week × Month heatmap...")

fig1, axes = plt.subplots(1, 2, figsize=(24, 8))
fig1.suptitle('Spending Patterns: Day-of-Week × Month', fontsize=16, fontweight='bold', y=1.02)

# Heatmap of total spending
pivot_amount = debits.pivot_table(values='Amount', index='DayOfWeek', columns='Month',
                                   aggfunc='sum', fill_value=0).reindex(dow_order)
pivot_amount.columns = [str(c) for c in pivot_amount.columns]

ax1 = axes[0]
sns.heatmap(pivot_amount / 1000, annot=True, fmt='.1f', cmap='YlOrRd',
            linewidths=0.5, ax=ax1, cbar_kws={'label': 'Amount (K Rs.)'},
            annot_kws={'size': 7})
ax1.set_title('Total Spending (thousands)', fontsize=13, fontweight='bold')
ax1.set_ylabel('')
ax1.set_xlabel('Month')
ax1.tick_params(axis='x', rotation=45, labelsize=8)

# Heatmap of transaction count
pivot_count = debits.pivot_table(values='Amount', index='DayOfWeek', columns='Month',
                                  aggfunc='count', fill_value=0).reindex(dow_order)
pivot_count.columns = [str(c) for c in pivot_count.columns]

ax2 = axes[1]
sns.heatmap(pivot_count, annot=True, fmt='.0f', cmap='YlGnBu',
            linewidths=0.5, ax=ax2, cbar_kws={'label': 'Number of Transactions'},
            annot_kws={'size': 7})
ax2.set_title('Transaction Count', fontsize=13, fontweight='bold')
ax2.set_ylabel('')
ax2.set_xlabel('Month')
ax2.tick_params(axis='x', rotation=45, labelsize=8)

plt.tight_layout()
fig1.savefig(str(REPORTS_DIR / "extra_heatmap.png"), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("  [OK] extra_heatmap.png")


# ═══════════════════════════════════════════════════════════════════
# FIGURE 2: Category Trends + Scatter + Weekend/Weekday
# ═══════════════════════════════════════════════════════════════════
print("\n[2/3] Category trends, scatter plot, weekend analysis...")

fig2 = plt.figure(figsize=(24, 36))
fig2.suptitle('Deep Dive: Trends, Patterns & Behavioral Insights',
              fontsize=16, fontweight='bold', y=0.995)

gs = gridspec.GridSpec(5, 2, hspace=0.40, wspace=0.30, top=0.97, bottom=0.02, left=0.08, right=0.95)

# --- Chart 1: Category stacked area over time ---
ax1 = fig2.add_subplot(gs[0, :])
cat_monthly = debits.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0)
cat_monthly.index = cat_monthly.index.to_timestamp()
# Order by total
cat_order = cat_monthly.sum().sort_values(ascending=False).index
cat_monthly = cat_monthly[cat_order]
colors_area = sns.color_palette("Set2", len(cat_monthly.columns))
ax1.stackplot(cat_monthly.index, [cat_monthly[c].values for c in cat_monthly.columns],
              labels=cat_monthly.columns, colors=colors_area, alpha=0.85)
ax1.set_title('Category Spending Over Time (Stacked Area)', fontsize=14, fontweight='bold')
ax1.set_ylabel('Amount (Rs.)')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax1.legend(loc='upper left', fontsize=8, ncol=3, framealpha=0.9)
ax1.tick_params(axis='x', rotation=45)

# --- Chart 2: Category month-over-month trend (line chart) ---
ax2 = fig2.add_subplot(gs[1, :])
# Focus on top 5 categories
top5_cats = cat_order[:5]
for cat, color in zip(top5_cats, colors_area[:5]):
    vals = cat_monthly[cat]
    # Rolling 3-month average
    rolling = vals.rolling(3, min_periods=1).mean()
    ax2.plot(vals.index, vals.values, alpha=0.3, color=color, linewidth=1)
    ax2.plot(rolling.index, rolling.values, color=color, linewidth=2.5, label=cat)
ax2.set_title('Top 5 Categories — Monthly Trend (3-month rolling avg)', fontsize=14, fontweight='bold')
ax2.set_ylabel('Amount (Rs.)')
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax2.legend(fontsize=9, loc='upper left')
ax2.tick_params(axis='x', rotation=45)

# --- Chart 3: Transaction scatter (date × amount, colored by category) ---
ax3 = fig2.add_subplot(gs[2, 0])
scatter_cats = debits['Category'].unique()
cat_color_map = {c: plt.cm.Set2(i / len(scatter_cats)) for i, c in enumerate(scatter_cats)}
for cat in scatter_cats:
    subset = debits[debits['Category'] == cat]
    ax3.scatter(subset['Datetime'], subset['Amount'], alpha=0.4, s=12,
                color=cat_color_map[cat], label=cat, edgecolors='none')
ax3.set_title('Every Transaction: Date vs Amount', fontsize=14, fontweight='bold')
ax3.set_ylabel('Amount (Rs.)')
ax3.set_xlabel('Date')
ax3.tick_params(axis='x', rotation=45)
ax3.legend(fontsize=7, loc='upper left', ncol=2, framealpha=0.9)
ax3.set_yscale('log')
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax3.set_title('Every Transaction (Log Scale)', fontsize=14, fontweight='bold')

# --- Chart 4: Weekend vs Weekday spending ---
ax4 = fig2.add_subplot(gs[2, 1])
weekend_data = debits.groupby('IsWeekend').agg(
    Total=('Amount', 'sum'),
    Count=('Amount', 'count'),
    Avg=('Amount', 'mean')
)
labels_w = ['Weekday', 'Weekend']
totals_w = [weekend_data.loc[False, 'Total'], weekend_data.loc[True, 'Total']]
counts_w = [weekend_data.loc[False, 'Count'], weekend_data.loc[True, 'Count']]
# Normalize by number of months to get monthly avg
n_months = debits['Month'].nunique()
weekly_avg = [t / (n_months * 5) for t in totals_w]  # ~5 weekdays/weekend-days per month
x = np.arange(2)
bars1 = ax4.bar(x - 0.15, [t for t in totals_w], 0.3, label='Total Spent', color='steelblue', alpha=0.8)
ax4_twin = ax4.twinx()
bars2 = ax4_twin.bar(x + 0.15, [c for c in counts_w], 0.3, label='Txn Count', color='coral', alpha=0.8)
ax4.set_xticks(x)
ax4.set_xticklabels(labels_w, fontsize=11)
ax4.set_ylabel('Total Spent (Rs.)', color='steelblue')
ax4_twin.set_ylabel('Transaction Count', color='coral')
ax4.set_title('Weekend vs Weekday', fontsize=14, fontweight='bold')
for b, v in zip(bars1, totals_w):
    ax4.text(b.get_x() + b.get_width()/2, v + 500, f'Rs.{v:,.0f}',
             ha='center', fontsize=9, fontweight='bold', color='steelblue')
for b, v in zip(bars2, counts_w):
    ax4_twin.text(b.get_x() + b.get_width()/2, v + 10, str(int(v)),
                  ha='center', fontsize=9, fontweight='bold', color='coral')
lines1, labels1 = ax4.get_legend_handles_labels()
lines2, labels2 = ax4_twin.get_legend_handles_labels()
ax4.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='upper right')

# --- Chart 5: Month-over-month growth rate ---
ax5 = fig2.add_subplot(gs[3, 0])
monthly_total = debits.groupby('Month')['Amount'].sum()
mom_pct = monthly_total.pct_change() * 100
mom_pct = mom_pct.dropna()
mom_ts = mom_pct.index.to_timestamp()
bar_colors = ['#2ecc71' if v > 0 else '#e74c3c' for v in mom_pct.values]
ax5.bar(mom_ts, mom_pct.values, color=bar_colors, width=25, alpha=0.8, edgecolor='white')
ax5.axhline(y=0, color='black', linewidth=0.8)
ax5.set_title('Month-over-Month % Change', fontsize=14, fontweight='bold')
ax5.set_ylabel('% Change')
ax5.tick_params(axis='x', rotation=45, labelsize=8)
for date, val in zip(mom_ts, mom_pct.values):
    if abs(val) > 40:
        ax5.text(date, val + (3 if val > 0 else -5), f'{val:.0f}%',
                 ha='center', fontsize=7, fontweight='bold',
                 color='#2ecc71' if val > 0 else '#e74c3c')

# --- Chart 6: Payee diversity over time ---
ax6 = fig2.add_subplot(gs[3, 1])
payees_per_month = debits.groupby('Month')['Transaction Details'].nunique()
payees_ts = payees_per_month.index.to_timestamp()
ax6.fill_between(payees_ts, payees_per_month.values, alpha=0.2, color='purple')
ax6.plot(payees_ts, payees_per_month.values, color='purple', linewidth=2, marker='o', markersize=4)
avg_div = payees_per_month.mean()
ax6.axhline(y=avg_div, color='orange', linestyle='--', linewidth=1.2, alpha=0.8,
            label=f'Avg: {avg_div:.0f} payees/month')
ax6.set_title('Payee Diversity Over Time', fontsize=14, fontweight='bold')
ax6.set_ylabel('Unique Payees per Month')
ax6.legend(fontsize=9)
ax6.tick_params(axis='x', rotation=45)

# --- Chart 7: Category concentration (top payee %) ---
ax7 = fig2.add_subplot(gs[4, 0])
cat_conc = {}
for cat in debits['Category'].unique():
    cat_df = debits[debits['Category'] == cat]
    top_payee_share = cat_df.groupby('Transaction Details')['Amount'].sum()
    top1_share = top_payee_share.max() / top_payee_share.sum() * 100
    top3_share = top_payee_share.nlargest(3).sum() / top_payee_share.sum() * 100
    cat_conc[cat] = {'Top 1 %': top1_share, 'Top 3 %': top3_share}

conc_df = pd.DataFrame(cat_conc).T.sort_values('Top 3 %', ascending=True)
x_pos = range(len(conc_df))
bars_top1 = ax7.barh([i + 0.15 for i in x_pos], conc_df['Top 1 %'], 0.3,
                      label='Top 1 Payee %', color='coral', alpha=0.8)
bars_top3 = ax7.barh([i - 0.15 for i in x_pos], conc_df['Top 3 %'], 0.3,
                      label='Top 3 Payees %', color='steelblue', alpha=0.8)
ax7.set_yticks(list(x_pos))
ax7.set_yticklabels(conc_df.index, fontsize=9)
ax7.set_title('Category Concentration: How Dominant is Top Payee?', fontsize=14, fontweight='bold')
ax7.set_xlabel('% of Category Total')
ax7.legend(fontsize=9)
for b, v in zip(bars_top1, conc_df['Top 1 %'].values):
    ax7.text(v + 1, b.get_y() + b.get_height(), f'{v:.0f}%', va='center', fontsize=8)

# --- Chart 8: Spending by time of day ---
ax8 = fig2.add_subplot(gs[4, 1])
hourly = debits.groupby('HourOfDay').agg(
    Total=('Amount', 'sum'),
    Count=('Amount', 'count')
)
time_labels = ['12a'] + [f'{h}a' for h in range(1,12)] + ['12p'] + [f'{h}p' for h in range(1,12)]
hourly_idx = range(24)
ax8_twin = ax8.twinx()
bars_h = ax8.bar(hourly_idx, hourly.reindex(range(24), fill_value=0)['Total'].values,
                 color='steelblue', alpha=0.7, label='Total Spent')
bars_c = ax8_twin.plot(hourly_idx, hourly.reindex(range(24), fill_value=0)['Count'].values,
                        color='coral', linewidth=2, marker='o', markersize=4, label='Txn Count')
ax8.set_xticks(hourly_idx)
ax8.set_xticklabels(time_labels, fontsize=7, rotation=45)
ax8.set_ylabel('Total Spent (Rs.)', color='steelblue')
ax8_twin.set_ylabel('Transaction Count', color='coral')
ax8.set_title('Spending by Hour of Day', fontsize=14, fontweight='bold')
lines1, labels1 = ax8.get_legend_handles_labels()
lines2, labels2 = ax8_twin.get_legend_handles_labels()
ax8.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='upper right')

chart2_path = REPORTS_DIR / "extra_insights.png"
plt.savefig(str(chart2_path), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"  [OK] {chart2_path}")


# ═══════════════════════════════════════════════════════════════════
# FIGURE 3: Weekly rolling spend + spending streaks
# ═══════════════════════════════════════════════════════════════════
print("\n[3/3] Weekly rolling + spending streaks...")

fig3, axes3 = plt.subplots(2, 1, figsize=(20, 12))
fig3.suptitle('Spending Rhythm: Weekly Averages & Streaks',
              fontsize=16, fontweight='bold')

# Weekly rolling
daily_total = debits.groupby('Datetime')['Amount'].sum()
daily_total = daily_total.sort_index()
weekly_rolling = daily_total.rolling(7, min_periods=1).mean()
ax_w = axes3[0]
ax_w.fill_between(daily_total.index, daily_total.values, alpha=0.15, color='steelblue', label='Daily spend')
ax_w.plot(weekly_rolling.index, weekly_rolling.values, color='darkorange', linewidth=2.5, label='7-day rolling avg')
overall_avg = daily_total.mean()
ax_w.axhline(y=overall_avg, color='red', linestyle='--', linewidth=1, alpha=0.7,
             label=f'Daily avg: Rs.{overall_avg:,.0f}')
ax_w.set_title('Daily Spend with 7-Day Rolling Average', fontsize=14, fontweight='bold')
ax_w.set_ylabel('Amount (Rs.)')
ax_w.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax_w.legend(fontsize=10)
ax_w.tick_params(axis='x', rotation=45)

# Spending streaks (consecutive days with spending above average)
above_avg = daily_total > overall_avg
streaks = []
current_streak = 0
streak_start = None
for date, is_above in above_avg.items():
    if is_above:
        current_streak += 1
        if current_streak == 1:
            streak_start = date
    else:
        if current_streak >= 3:
            streaks.append((streak_start, date, current_streak))
        current_streak = 0
if current_streak >= 3:
    streaks.append((streak_start, above_avg.index[-1], current_streak))

ax_s = axes3[1]
# Color each day: green = below avg, red = above avg
bar_colors_s = ['#e74c3c' if daily_total[d] > overall_avg else '#2ecc71' for d in daily_total.index]
ax_s.bar(daily_total.index, daily_total.values, color=bar_colors_s, alpha=0.7, width=1.0)
ax_s.axhline(y=overall_avg, color='red', linestyle='--', linewidth=1, alpha=0.7)
# Annotate long streaks
for start, end, length in streaks:
    ax_s.axvspan(start, end, alpha=0.15, color='red')
    mid = start + (end - start) / 2
    total_in_streak = daily_total[start:end].sum()
    ax_s.annotate(f'{length}-day streak\nRs.{total_in_streak:,.0f}',
                  xy=(mid, daily_total[start:end].max()),
                  xytext=(mid, daily_total[start:end].max() * 1.15),
                  arrowprops=dict(arrowstyle='->', color='darkred', lw=1.2),
                  fontsize=8, color='darkred', ha='center', fontweight='bold')
ax_s.set_title('Daily Spending Streaks (Red = above average, Green = below)',
               fontsize=14, fontweight='bold')
ax_s.set_ylabel('Amount (Rs.)')
ax_s.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
ax_s.tick_params(axis='x', rotation=45)

plt.tight_layout()
chart3_path = REPORTS_DIR / "extra_weekly_streaks.png"
plt.savefig(str(chart3_path), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"  [OK] {chart3_path}")


# ═══════════════════════════════════════════════════════════════════
# Quick summary
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Extra insights generated!")
print("=" * 60)

print("\n--- Weekend vs Weekday ---")
wkday = debits[~debits['IsWeekend']]
wkend = debits[debits['IsWeekend']]
n_m = debits['Month'].nunique()
print(f"  Weekday: Rs.{wkday['Amount'].sum():>10,.0f} across {len(wkday)} txns (avg Rs.{wkday['Amount'].sum()/n_m:,.0f}/month)")
print(f"  Weekend: Rs.{wkend['Amount'].sum():>10,.0f} across {len(wkend)} txns (avg Rs.{wkend['Amount'].sum()/n_m:,.0f}/month)")
print(f"  Avg weekday txn: Rs.{wkday['Amount'].mean():.0f}")
print(f"  Avg weekend txn: Rs.{wkend['Amount'].mean():.0f}")

print("\n--- Payee Diversity Trend ---")
first_half = debits[debits['Month'] <= '2025-06']
second_half = debits[debits['Month'] > '2025-06']
print(f"  Jun 2024 - Jun 2025: {first_half['Transaction Details'].nunique()} unique payees")
print(f"  Jul 2025 - Jul 2026: {second_half['Transaction Details'].nunique()} unique payees")

print("\n--- Category Concentration ---")
for cat in conc_df.sort_values('Top 3 %', ascending=False).index:
    top1 = conc_df.loc[cat, 'Top 1 %']
    top3 = conc_df.loc[cat, 'Top 3 %']
    print(f"  {cat:<30} Top1={top1:.0f}%  Top3={top3:.0f}%")

print("\n--- Hour of Day ---")
peak_hour = hourly['Total'].idxmax()
print(f"  Peak spending hour: {peak_hour}:00 (Rs.{hourly.loc[peak_hour, 'Total']:,.0f})")
night = hourly.reindex(range(0, 6), fill_value=0)['Total'].sum()
day = hourly.reindex(range(6, 18), fill_value=0)['Total'].sum()
evening = hourly.reindex(range(18, 24), fill_value=0)['Total'].sum()
total_all = hourly['Total'].sum()
print(f"  Night (12a-6a):  Rs.{night:>8,.0f} ({night/total_all*100:.1f}%)")
print(f"  Day (6a-6p):     Rs.{day:>8,.0f} ({day/total_all*100:.1f}%)")
print(f"  Evening (6p-12a): Rs.{evening:>8,.0f} ({evening/total_all*100:.1f}%)")

if streaks:
    print("\n--- Spending Streaks (3+ days above average) ---")
    for start, end, length in streaks:
        total_s = daily_total[start:end].sum()
        print(f"  {start.strftime('%d %b')} to {end.strftime('%d %b %Y')}: {length} days, Rs.{total_s:,.0f}")

print(f"\nFiles saved to: {REPORTS_DIR}")
