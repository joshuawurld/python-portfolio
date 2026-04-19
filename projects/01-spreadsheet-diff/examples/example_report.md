# Spreadsheet Diff Report

- **File A:** `tests/fixtures/file_a.csv`
- **File B:** `tests/fixtures/file_b.csv`
- **Key column:** `ID`

## Result: DIFFERENCES FOUND

## Shape
- File A: 4 rows x 4 columns
- File B: 4 rows x 4 columns

## Headers
- Headers match (same names, same order).

## Row Membership
- Rows only in A: 1
- Rows only in B: 1

### First rows only in A
- {'ID': 4, 'Name': 'Delta', 'Amount': 400, 'Currency': 'GBP'}

### First rows only in B
- {'ID': 5, 'Name': 'Echo', 'Amount': 500, 'Currency': 'GBP'}

## Cell Differences
- Value mismatches: 2
- Type mismatches: 0

### Value mismatches (first 20)
| Row | Column | File A | File B |
|---|---|---|---|
| 0 | Amount | np.int64(100) | np.int64(150) |
| 2 | Currency | 'GBP' | 'USD' |
