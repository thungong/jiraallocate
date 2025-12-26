# 💰 VAT Toggle Functionality - How It Works

## Overview

The "Include VAT in calculations" toggle controls **which amount column** to extract from the invoice PDF.

---

## 🎯 How It Works

### When **Unchecked** (Exclude VAT - Default):
```
📊 Calculation Mode: Exclude VAT
- Using Amount excl. tax column (excludes VAT)
- For invoices with multiple amount columns, this selects the amount without tax
```

**Behavior:**
- **Text Extraction:** Takes the **FIRST** USD amount found on each line
- **Table Extraction:** Looks for column header with "excl" or "tax" keywords
- **Auto-detect:** If no header match, uses **first/leftmost** amount column

**Example Invoice Line:**
```
Confluence (Cloud)  x 30  USD 12.00  USD 1.20  USD 13.20
                           ^^^^^^^^   ^^^^^^^^  ^^^^^^^^
                           Unit Price  Tax      Total
                           [SELECTED]
```

### When **Checked** (Include VAT):
```
📊 Calculation Mode: Include VAT ✅
- Using rightmost/final Amount column (includes VAT)
- For invoices with multiple amount columns, this selects the total with tax
```

**Behavior:**
- **Text Extraction:** Takes the **LAST** USD amount found on each line
- **Table Extraction:** Looks for "amount" column WITHOUT "excl" keyword
- **Auto-detect:** If no header match, uses **last/rightmost** amount column

**Example Invoice Line:**
```
Confluence (Cloud)  x 30  USD 12.00  USD 1.20  USD 13.20
                           ^^^^^^^^   ^^^^^^^^  ^^^^^^^^
                           Unit Price  Tax      Total
                                                [SELECTED]
```

---

## 📊 Implementation Details

### 1. Text Extraction (`extract_invoice_items`)

```python
# Extract all USD amounts from the line
matches = re.findall(r"USD\s*([\d,]+\.\d{2})", line)
amounts = [float(m.replace(',', '')) for m in matches]

if include_vat:
    # Take the LAST amount (rightmost = total with VAT)
    amount = amounts[-1]
else:
    # Take the FIRST amount (Amount excl. tax)
    amount = amounts[0]
```

**Logic:**
- Find ALL USD amounts in a line
- Select first or last based on toggle
- Works for lines with 1, 2, or more amounts

### 2. Table Extraction (`extract_invoice_items_from_tables`)

```python
# Find amount column based on VAT setting
if include_vat:
    # Look for "Amount" column (without "excl")
    if 'amount' in cell_lower and 'excl' not in cell_lower:
        amount_col_idx = idx
else:
    # Look for "Amount excl. tax"
    if 'amount' in cell_lower and 'excl' in cell_lower:
        amount_col_idx = idx
```

**Auto-detection fallback:**
```python
# If no header match, detect all amount columns
if amount_col_idx is None:
    amount_columns = find_all_amount_columns()
    
    if include_vat:
        # Use rightmost (last) amount column
        amount_col_idx = amount_columns[-1]
    else:
        # Use leftmost (first) amount column
        amount_col_idx = amount_columns[0]
```

---

## 🔍 Visual Examples

### PDF Format 1: Old Format (Single Amount Column)
```
Description              | Quantity | Amount excl. tax
Confluence              | 30       | USD 12.41
draw.io                 | 30       | USD 55.37
```

**Result (Unchecked):** ✅ $12.41, $55.37  
**Result (Checked):** ✅ $12.41, $55.37 (same, only one column)

---

### PDF Format 2: New Format (Multiple Amount Columns)
```
Description         | Qty | Unit Price | Tax      | Amount
Confluence         | 30  | USD 12.00  | USD 1.20 | USD 13.20
draw.io            | 30  | USD 50.00  | USD 5.00 | USD 55.00
```

**Result (Unchecked - Exclude VAT):**
- Looks for "Amount excl. tax" column → not found
- Falls back to first amount column → Unit Price
- ✅ $12.00, $50.00

**Result (Checked - Include VAT):**
- Looks for "Amount" column (final) → found!
- ✅ $13.20, $55.00

---

### PDF Format 3: Explicit Labels
```
Description         | Qty | Amount excl. tax | VAT      | Amount
Confluence         | 30  | USD 12.00        | USD 1.20 | USD 13.20
draw.io            | 30  | USD 50.00        | USD 5.00 | USD 55.00
```

**Result (Unchecked - Exclude VAT):**
- Finds "Amount excl. tax" column
- ✅ $12.00, $50.00

**Result (Checked - Include VAT):**
- Finds "Amount" column (rightmost)
- ✅ $13.20, $55.00

---

## ✅ Verification

### How to verify it's working correctly:

1. **Check the Calculation Mode message:**
   ```
   📊 Calculation Mode: Include VAT ✅
   - Using rightmost/final Amount column (includes VAT)
   ```

2. **View Extraction Details:**
   - Click "🔍 View Extraction Details" expander
   - Check extracted amounts
   - Compare with PDF

3. **Check Invoice Summary:**
   ```
   📋 Invoice Summary: 6 line items | Total Amount: $692.49
   ```
   - This total should match the invoice total
   - If unchecked: should match subtotal (before tax)
   - If checked: should match grand total (with tax)

4. **Compare totals:**
   ```
   🧮 Calculated Grand Total: $692.49
   ```
   - Should equal Invoice Summary total
   - Verify against PDF invoice total

---

## 🎯 Use Cases

### Use Case 1: You want to allocate WITHOUT tax
```
✅ Uncheck "Include VAT in calculations"
→ Extracts amounts excluding VAT
→ Total will be lower (pre-tax)
→ Use this if your company handles VAT separately
```

### Use Case 2: You want to allocate WITH tax
```
✅ Check "Include VAT in calculations"
→ Extracts amounts including VAT
→ Total will be higher (with tax)
→ Use this if you allocate the final amount charged
```

### Use Case 3: Invoice has only one amount column
```
Toggle doesn't matter - both give same result
→ Extract the only amount available
→ Check PDF to verify if it includes VAT or not
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Total doesn't match invoice
**Cause:** Wrong VAT toggle setting

**Solution:**
1. Look at your PDF invoice
2. Find the grand total line
3. Check if extracted total matches
4. If not, toggle the VAT checkbox
5. Re-process

### Issue 2: Amounts look too high/low
**Cause:** Extracting wrong column

**Solution:**
1. Open "View Extraction Details"
2. Check sample amounts
3. Compare with PDF (look at 1-2 lines)
4. Adjust VAT toggle if needed

### Issue 3: Not sure which to use
**Answer:**
1. Check your PDF structure:
   - **One amount column?** → Doesn't matter which
   - **Multiple columns?** → Check labels
   - **Has "excl. tax"?** → Uncheck for that column
   - **Has "Total" or "Amount"?** → Check for that column

2. Check your requirements:
   - **Accountant wants pre-tax amounts?** → Uncheck
   - **Need to allocate exact invoice total?** → Check

---

## 🔧 Technical Notes

### For Developers:

**Parameter flow:**
```
1. User toggles checkbox
   ↓
2. Stored in session_state['include_vat']
   ↓
3. Passed to extract_invoice_items(text, include_vat)
   ↓
4. Passed to extract_invoice_items_from_tables(pdf, include_vat)
   ↓
5. Controls column selection logic
```

**Key variables:**
- `include_vat`: Boolean from checkbox
- `amounts`: List of all USD amounts found
- `amount_col_idx`: Index of column to use in tables
- `amount`: Final selected amount for each product

**Testing:**
```python
# Test with sample line
line = "Product x 10 USD 100.00 USD 10.00 USD 110.00"

# include_vat=False → 100.00 (first)
# include_vat=True → 110.00 (last)
```

---

## ✨ Summary

| Setting | Column Selected | Use When |
|---------|----------------|----------|
| ☐ Unchecked | First/leftmost amount (excl. VAT) | You want pre-tax amounts |
| ☑️ Checked | Last/rightmost amount (incl. VAT) | You want final charged amounts |

**Key Points:**
- ✅ Works with both text and table extraction
- ✅ Auto-detects column based on headers
- ✅ Falls back to position if headers unclear
- ✅ Clearly shows which mode is active
- ✅ Total reflects the selected amounts

**Always verify:** Check that extracted total matches the expected invoice total! 💰

---

Last updated: December 26, 2025
