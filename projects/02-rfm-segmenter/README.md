# Customer Segmenter (RFM)

A small Python tool that reads customer purchase data and splits customers into groups based on how valuable they are. Marketing teams use this to decide who gets which offer.

## What problem this solves

Marketing teams often blast the same message to everyone. That's wasteful. This tool helps them:
- Find the big spenders who just bought (send them loyalty perks)
- Find the once-regulars who've gone quiet (win them back)
- Find the bargain hunters (send them discount codes)

## How it works (the simple version)

For every customer, we calculate three scores from 1–5:
- **R**ecency — how recently did they buy? (5 = last week, 1 = 2 years ago)
- **F**requency — how often do they buy? (5 = every week, 1 = once ever)
- **M**onetary — how much have they spent total? (5 = £5k+, 1 = £50)

Then we combine R+F+M into a score (3–15) and label the customer:
| Score | Label | Typical action |
|-------|-------|----------------|
| 13–15 | Champions | VIP early access, referrals |
| 10–12 | Loyal | Upsell related products |
| 7–9 | At Risk | Re-engagement campaign |
| 3–6 | Lost / Hibernating | Aggressive discount or ignore |

## The data setup (two simple tables)

We need two CSVs:

**customers.csv** — who they are
```
customer_id,name,email,signup_date
C001,Alice Smith,alice@email.com,2023-01-15
C002,Bob Jones,bob@email.com,2022-08-03
```

**transactions.csv** — what they bought
```
transaction_id,customer_id,date,amount
T001,C001,2025-04-15,120.00
T002,C001,2025-03-10,85.50
T003,C002,2024-01-20,45.00
```

That's it. Two tables, one join, three calculations.

## Quick start

```bash
cd projects/02-rfm-segmenter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run with example data
python -m src.segment examples/customers.csv examples/transactions.csv --output segments.csv
```

## Output

A CSV with one row per customer:
```
customer_id,r_score,f_score,m_score,rfm_score,segment
C001,5,4,4,13,Champions
C002,1,1,1,3,Lost
```

Marketing can import this straight into their CRM or email tool and target each segment differently.

## Status

Work in progress — core scoring logic implemented, CLI and reporting in progress.
