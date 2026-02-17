# Payslip (Contracheque) — Extraction Reference

## Overview

Payslip documents list employee earnings (vencimentos) and deductions (descontos) in a tabular format.
Each variant handles a different visual layout but extracts the same core data structure.

## Common Output Fields

| Field | Description |
|-------|-------------|
| `MES_ANO` | Reference month/year (e.g., `01/2025`) |
| `codigo` | Numeric code identifying the earning/deduction |
| `descricao` | Text description (e.g., "Salário Base", "INSS") |
| `referencia` | Quantity or reference value (hours, days, rate) |
| `vencimento` | Earning amount (positive) |
| `desconto` | Deduction amount (negative) |

## Variant Details

### black-default-1 (Standard Space-Delimited)
- **Date format**: `MM/YYYY` extracted from header
- **Column separator**: Whitespace (spaces)
- **Table detection**: Starts at "Cód Descrição" row, ends at "TOTAIS"
- **Parsing**: Regex splits code (3-4 digits) from description, then extracts monetary values `\d{1,3}(\.\d{3})*,\d{2}`
- **Discount detection**: Keywords like INSS, IRRF, VALE, DESCONTO in description

### black-default-2 (Alternate Keywords)
- **Same as default-1** but with different discount identification keywords
- **Additional keywords**: "ARREDONDAMENTO", "CONTRIBUIÇÃO"
- **Month extraction**: Slightly different regex for header line

### black-default-3 (Pipe-Delimited with JAN/YYYY)
- **Date format**: `JAN/2025` (textual month abbreviation)
- **Column separator**: Pipe character (`|`)
- **Table detection**: Section ends at "BASE/OUTROS" marker
- **Parsing**: Split by `|` → [Code+Desc | Ref | Vencimentos | Descontos]

### black-broken-duplicated-1 (Belshop Format)
- **Date format**: "Mensalista Março de 2023" (full month name)
- **Inverted text**: Detects and removes reversed OCR text (e.g., "obicer" → "recibo")
- **Word grouping**: Groups by Y-coordinate for proper line assembly
- **Dedup**: Stops processing at second "Código Descrição" header (duplicate section)
- **Column separator**: Space-based with value extraction from end of line

### black-default-duplicated-1/2/3 (Duplicate Handling)
- **Same layout as default** but document contains duplicate payslip per page
- **Strategy**: Tracks processed descriptions to avoid counting twice
- **Conflict resolution**: Keeps higher value when duplicates found

### black-default-two-in-one-1/2 (Two Payslips Per Page)
- **Two distinct payslips** printed on same physical page
- **Split logic**: Detects second header to separate data sets
- **Output**: Merges both into consolidated period view

### black-secrecy-1 (Confidential Layout)
- **Restricted fields**: Some columns masked or hidden
- **Parsing**: Adapts to missing columns gracefully
- **Fallback**: Uses available data without requiring full row structure

### blue-default-1/2 (Blue-Themed)
- **Same extraction logic** as black-default variants
- **Visual difference only**: Blue header/border (relevant for image-based detection)
- **Column mapping**: Slight variations in column order
