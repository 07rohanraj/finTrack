"""
Spending Dashboard — Backend Server
No external dependencies. Uses only Python stdlib + pandas + openpyxl.
Run: python server.py
Open: http://localhost:8420
"""
import json
import sys
import os
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

import pandas as pd

# ── Configuration ────────────────────────────────────────────────
PORT = 8420
EXCEL_PATH = Path(__file__).parent.parent / "TransactionStatement.xlsx"
STATIC_DIR = Path(__file__).parent / "static"

EXCLUDE = {'Personal Transfers', 'Investment', 'Bank Transfer'}

CATEGORY_RULES = [
    (['upstox', 'icici prudential', 'zerodha', 'groww'], 'Investment'),
    (['bmtc', 'bmrc', 'metro rail', 'bangalore metro', 'petrol', 'diesel',
      'yash anand fuel', 'krishna petroleum', 'dharamaa service'], 'Transport & Fuel'),
    (['jio', 'airtel', 'prepaid recharg'], 'Mobile Recharge'),
    (['myntra', 'flipkart', 'amazon', 'meesho', 'zepto', 'zudio', 'ajio',
      'nykaa', 'tata cliq', 'ekart', 'anuyojya', 'city enterprises', 'garment'],
     'Shopping & E-Commerce'),
    (['google play', 'google india digital', 'youtube', 'netflix', 'hotstar',
      'spotify', 'kukufm', 'testbook', 'bookmyshow', 'razorpay'],
     'Subscriptions & Digital'),
    (['shaadi ki biryani', 'shaad ki', 'biryani', 'hotel', 'restaurant',
      'cafe', 'coffee', 'pizza', 'bakery', 'food', 'juice', 'tea', 'momos',
      'morning star', 'hungry heist', 'pappu nishad', 'richmond soft',
      'soft drink', 'krishna food', 'sivam bengali', 'j and b kitchen',
      'green theory', 'varaha cafe', 'tea break', 'chirus', 'ponlait',
      'milon juice', 'divya juice', 'juice bar', 'fruit shope',
      'bharathi fast', 'y v tea', 'quick pick coffee', 'kannamma fruit',
      'amman fruit', 'sbm store', 'city store', 'sri ganga', 'sri vinayaka',
      'sri brahmalingeswara', 'bhrama lingeshwara', 'sri neevi', 'y v tea shop'],
     'Food & Dining'),
    (['mangalore fresh', 'manglore fresh', 'sagaya raj', 'nandhini',
      'star bazaar', 'supermarket', 'royal mart', 'vegetable', 'fruit',
      'coconut', 'condiment', 'groceries', 'amazon pay groceries',
      'pan shop', 'olive mart', 'chaithra', 'kamakshi', 'doddamma',
      'sri durga', 'mother dairy', 'sri lakshmi', 'sri brahmalingeswara juice',
      'y v tea stall', 'kamakshi vegetable'], 'Groceries & Essentials'),
    (['medplus', 'medical', 'pharmacy', 'fatima', 'mamtha',
      'sachin medical', 'sanjay medical'], 'Medical & Health'),
    (['irctc', 'indian railways', 'train', 'flight', 'amazon flights',
      'redbus', 'paytm travel', 'palm suites'], 'Travel & Stays'),
    (['bank account'], 'Bank Transfer'),
    (['bill paid', 'credit card'], 'Credit Card Payment'),
    (['mithila time', 'optical', 'watch', 'salon', 'saloon',
      'gents parlour', 'barber'], 'Personal Care'),
    (['electricity', 'water bill', 'gas bill', 'broadband', 'wifi'], 'Utilities'),
]

CATEGORY_COLORS = {
    'Shopping & E-Commerce': '#6c5ce7',
    'Food & Dining':         '#e17055',
    'Groceries & Essentials':'#00b894',
    'Transport & Fuel':      '#74b9ff',
    'Travel & Stays':        '#fdcb6e',
    'Mobile Recharge':       '#a29bfe',
    'Subscriptions & Digital':'#fd79a8',
    'Credit Card Payment':   '#636e72',
    'Personal Care':         '#fab1a0',
    'Medical & Health':      '#00cec9',
    'Utilities':             '#ffeaa7',
}


# ── Data Processing ──────────────────────────────────────────────
def categorize(payee: str) -> str:
    p = payee.lower()
    for keywords, category in CATEGORY_RULES:
        if any(k in p for k in keywords):
            return category
    return 'Personal Transfers'


def load_data():
    print(f"Loading {EXCEL_PATH}...")
    t0 = time.time()
    df = pd.read_excel(str(EXCEL_PATH))
    df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
    df['HourOfDay'] = pd.to_datetime(df['Time'], format='%I:%M %p').dt.hour
    df['IsWeekend'] = df['Datetime'].dt.dayofweek >= 5
    df['DayName'] = df['Datetime'].dt.day_name()
    df['MonthStr'] = df['Datetime'].dt.strftime('%Y-%m')
    df['DateStr'] = df['Datetime'].dt.strftime('%Y-%m-%d')
    df['QuarterStr'] = df['Datetime'].dt.to_period('Q').astype(str)
    df['DayNum'] = df['Datetime'].dt.dayofweek

    all_debits = df[df['Type'] == 'Debit'].copy()
    all_debits['Category'] = all_debits['Transaction Details'].apply(categorize)
    all_debits['CleanName'] = (
        all_debits['Transaction Details']
        .str.replace(r'^Paid to ', '', regex=True)
        .str.replace(r'^Paid ', '', regex=True)
    )

    # Keep ALL data including excluded categories (for transparency)
    all_records = []
    for _, row in all_debits.iterrows():
        all_records.append({
            'id': int(_),
            'date': row['DateStr'],
            'month': row['MonthStr'],
            'quarter': row['QuarterStr'],
            'time': row['Time'],
            'hour': int(row['HourOfDay']),
            'dayNum': int(row['DayNum']),
            'day': row['DayName'],
            'name': row['CleanName'],
            'amount': round(float(row['Amount']), 2),
            'category': row['Category'],
            'txnId': row['Transaction ID'],
            'utr': row['UTR No'],
            'weekend': bool(row['IsWeekend']),
            'excluded': row['Category'] in EXCLUDE
        })

    # Also prepare filtered (actual spending only) view
    actual = [r for r in all_records if not r['excluded']]

    # Build aggregated endpoints
    categories = {}
    for r in actual:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'name': cat, 'total': 0, 'count': 0, 'items': [],
                               'color': CATEGORY_COLORS.get(cat, '#636e72')}
        categories[cat]['total'] = round(categories[cat]['total'] + r['amount'], 2)
        categories[cat]['count'] += 1

    # Sort categories by total descending
    sorted_cats = sorted(categories.values(), key=lambda c: -c['total'])
    total_spent = sum(c['total'] for c in sorted_cats)

    for c in sorted_cats:
        c['pct'] = round(c['total'] / total_spent * 100, 1) if total_spent else 0
        c['avg'] = round(c['total'] / c['count'], 2) if c['count'] else 0
        del c['items']  # Don't send in API

    # Monthly aggregation
    monthly_map = {}
    for r in actual:
        m = r['month']
        if m not in monthly_map:
            monthly_map[m] = {'month': m, 'total': 0, 'count': 0, 'categories': {}}
        monthly_map[m]['total'] = round(monthly_map[m]['total'] + r['amount'], 2)
        monthly_map[m]['count'] += 1
        cat = r['category']
        if cat not in monthly_map[m]['categories']:
            monthly_map[m]['categories'][cat] = 0
        monthly_map[m]['categories'][cat] = round(
            monthly_map[m]['categories'][cat] + r['amount'], 2)

    monthly = [monthly_map[k] for k in sorted(monthly_map.keys())]

    # Quarterly
    quarterly_map = {}
    for r in actual:
        q = r['quarter']
        if q not in quarterly_map:
            quarterly_map[q] = {'quarter': q, 'total': 0, 'count': 0}
        quarterly_map[q]['total'] = round(quarterly_map[q]['total'] + r['amount'], 2)
        quarterly_map[q]['count'] += 1
    quarterly = [quarterly_map[k] for k in sorted(quarterly_map.keys())]

    # Top payees
    payees_map = {}
    for r in actual:
        n = r['name']
        if n not in payees_map:
            payees_map[n] = {'name': n, 'total': 0, 'count': 0,
                             'category': r['category'], 'firstSeen': r['date'],
                             'lastSeen': r['date']}
        payees_map[n]['total'] = round(payees_map[n]['total'] + r['amount'], 2)
        payees_map[n]['count'] += 1
        if r['date'] < payees_map[n]['firstSeen']:
            payees_map[n]['firstSeen'] = r['date']
        if r['date'] > payees_map[n]['lastSeen']:
            payees_map[n]['lastSeen'] = r['date']

    top_payees = sorted(payees_map.values(), key=lambda p: -p['total'])[:30]

    # Hourly
    hourly = [0] * 24
    hourly_count = [0] * 24
    for r in actual:
        hourly[r['hour']] = round(hourly[r['hour']] + r['amount'], 2)
        hourly_count[r['hour']] += 1

    # Day of week
    dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow = [{'day': d, 'total': 0, 'count': 0, 'avg': 0} for d in dow_names]
    for r in actual:
        idx = r['dayNum']
        dow[idx]['total'] = round(dow[idx]['total'] + r['amount'], 2)
        dow[idx]['count'] += 1
    for d in dow:
        d['total'] = round(d['total'], 2)
        d['avg'] = round(d['total'] / d['count'], 2) if d['count'] else 0

    # Daily totals
    daily_map = {}
    for r in actual:
        d = r['date']
        if d not in daily_map:
            daily_map[d] = {'date': d, 'total': 0, 'count': 0, 'payees': set()}
        daily_map[d]['total'] = round(daily_map[d]['total'] + r['amount'], 2)
        daily_map[d]['count'] += 1
        daily_map[d]['payees'].add(r['name'])

    daily = []
    for k in sorted(daily_map.keys()):
        v = daily_map[k]
        daily.append({
            'date': v['date'], 'total': v['total'],
            'count': v['count'], 'payees': len(v['payees'])
        })

    # Months list
    months_list = sorted(set(r['month'] for r in all_records))
    categories_list = sorted(set(r['category'] for r in actual))

    # Summary stats
    n_months = len(set(r['month'] for r in actual))
    summary = {
        'totalSpent': round(total_spent, 2),
        'totalTxns': len(actual),
        'allTxns': len(all_records),
        'excludedTxns': len(all_records) - len(actual),
        'uniquePayees': len(payees_map),
        'avgTransaction': round(total_spent / len(actual), 2) if actual else 0,
        'monthlyAvg': round(total_spent / n_months, 2) if n_months else 0,
        'months': months_list,
        'categories': categories_list,
        'maxTxn': max(r['amount'] for r in actual) if actual else 0,
        'dateRange': [min(r['date'] for r in actual), max(r['date'] for r in actual)]
                     if actual else ['', '']
    }

    elapsed = time.time() - t0
    print(f"Loaded {len(all_records)} txns ({len(actual)} actual spending) in {elapsed:.2f}s")

    return {
        'summary': summary,
        'categories': sorted_cats,
        'monthly': monthly,
        'quarterly': quarterly,
        'topPayees': top_payees,
        'hourly': hourly,
        'hourlyCount': hourly_count,
        'dayOfWeek': dow,
        'daily': daily,
        'transactions': actual,  # actual spending only (for table)
    }


# ── HTTP Handler ─────────────────────────────────────────────────
DATA = None  # Global, loaded once


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/api/data':
            self._json_response(DATA)
        elif path == '/api/search':
            q = params.get('q', [''])[0].lower()
            if not q:
                self._json_response(DATA['transactions'][:50])
                return
            results = [t for t in DATA['transactions']
                       if q in t['name'].lower() or q in t['category'].lower()]
            results.sort(key=lambda x: -x['amount'])
            self._json_response(results[:100])
        else:
            super().do_GET()

    def _json_response(self, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if '/api/' in str(args[0]) if args else False:
            return  # Suppress API logs
        super().log_message(format, *args)


# ── Main ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    DATA = load_data()

    server = HTTPServer(('localhost', PORT), DashboardHandler)
    print(f"\nDashboard running at: http://localhost:{PORT}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
