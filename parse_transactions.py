import re
import pandas as pd
from pathlib import Path


def parse_phonepe_statement(filepath: str) -> pd.DataFrame:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f.readlines()]

    date_pattern = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2},\s+\d{4}$")
    time_pattern = re.compile(r"^\d{2}:\d{2}\s+(AM|PM)$")
    txn_id_pattern = re.compile(r"^Transaction ID\s*:\s*(.+)$")
    utr_pattern = re.compile(r"^UTR No\s*:\s*(.+)$")
    debit_credit_pattern = re.compile(r"^(Debit|Credit)\s+INR\s+([\d,]+\.?\d*)$")
    amount_only_pattern = re.compile(r"^([\d,]+\.\d{2})$")
    account_pattern = re.compile(r"^(Debited from|Credited to)\s+(.+)$")
    page_pattern = re.compile(r"^Page\s+\d+\s+of\s+\d+$")
    header_pattern = re.compile(r"^Date\s+Transaction\s+Details\s+Type\s+Amount$")

    skip_strings = {
        "Transaction Statement for",
        "This is an automatically generated statement",
        "errors in the statement at",
        "Visit https://www.phonepe.com",
        "/privacy-policy/",
        "Do not fall prey",
        "emails and calls.",
        "The contents of this email",
        "received this message by mistake",
        "the recipient's details are corrected.",
        "Customer(s) are requested",
        "PhonePe Terms",
    }

    transactions = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue
        if date_pattern.match(line):
            i += 1
            if i >= len(lines):
                break

            time_line = lines[i].strip() if i < len(lines) else ""
            if not time_pattern.match(time_line):
                i += 1
                continue
            i += 1

            txn_details = lines[i].strip() if i < len(lines) else ""
            i += 1

            txn_id = ""
            utr_no = ""
            account_info = ""
            txn_type = ""
            amount = ""

            while i < len(lines):
                current = lines[i].strip()

                if date_pattern.match(current):
                    break
                if page_pattern.match(current) or header_pattern.match(current):
                    i += 1
                    continue
                if any(current.startswith(s) for s in skip_strings):
                    i += 1
                    continue
                if not current:
                    i += 1
                    continue

                m_txnid = txn_id_pattern.match(current)
                if m_txnid:
                    txn_id = m_txnid.group(1).strip()
                    i += 1
                    continue

                m_utr = utr_pattern.match(current)
                if m_utr:
                    utr_no = m_utr.group(1).strip()
                    i += 1
                    continue

                m_acc = account_pattern.match(current)
                if m_acc:
                    account_info = m_acc.group(2).strip()
                    i += 1
                    continue

                m_dc = debit_credit_pattern.match(current)
                if m_dc:
                    txn_type = m_dc.group(1)
                    amount = m_dc.group(2).replace(",", "")
                    i += 1
                    continue

                m_dc_bare = re.match(r"^(Debit|Credit)\s+INR$", current)
                if m_dc_bare:
                    txn_type = m_dc_bare.group(1)
                    i += 1
                    if i < len(lines):
                        next_line = lines[i].strip()
                        m_next = amount_only_pattern.match(next_line)
                        if m_next:
                            amount = m_next.group(1).replace(",", "")
                            i += 1
                    continue

                m_amt = amount_only_pattern.match(current)
                if m_amt and not txn_type:
                    i += 1
                    continue

                if current in ("Credit", "Debit"):
                    txn_type = current
                    i += 1
                    if i < len(lines):
                        next_line = lines[i].strip()
                        m_next = amount_only_pattern.match(next_line)
                        if m_next:
                            amount = m_next.group(1).replace(",", "")
                            i += 1
                    continue

                i += 1

            transactions.append({
                "Date": line.strip(),
                "Time": time_line,
                "Transaction Details": txn_details,
                "Transaction ID": txn_id,
                "UTR No": utr_no,
                "Account": account_info,
                "Type": txn_type,
                "Amount": float(amount) if amount else 0.0,
            })
        else:
            i += 1

    df = pd.DataFrame(transactions)
    return df


def main():
    input_file = Path(__file__).parent / "TransactionStatement.md"
    output_file = Path(__file__).parent / "TransactionStatement.xlsx"

    print(f"Reading: {input_file}")
    df = parse_phonepe_statement(str(input_file))
    print(f"Parsed {len(df)} transactions")
    print(f"Debits: {len(df[df['Type'] == 'Debit'])}, Credits: {len(df[df['Type'] == 'Credit'])}")
    print(f"Total Debit Amount: Rs. {df[df['Type'] == 'Debit']['Amount'].sum():,.2f}")
    print(f"Total Credit Amount: Rs. {df[df['Type'] == 'Credit']['Amount'].sum():,.2f}")

    df.to_excel(str(output_file), index=False, engine="openpyxl")
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
