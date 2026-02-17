# Model References

Reference extraction scripts organized by document type and layout variant.  
Each variant contains a `code/conversion.py` with the parsing logic tailored to that specific document format.

## Structure

```
model-references/
├── payslip/           # Contracheque (Payslip) variants
│   ├── black-default-1/        → Space-delimited, MM/YYYY date, standard table
│   ├── black-default-2/        → Similar to default-1, different discount keywords
│   ├── black-default-3/        → Pipe-delimited ('|'), JAN/YYYY date, BASE/OUTROS marker
│   ├── black-broken-duplicated-1/ → Belshop format, inverted text handling, dedup logic
│   ├── black-default-duplicated-1/ → Handles duplicated payslips on same page
│   ├── black-default-duplicated-2/ → Variant with different dedup strategy
│   ├── black-default-duplicated-3/ → Third dedup variant
│   ├── black-default-two-in-one-1/ → Two payslips merged in one page
│   ├── black-default-two-in-one-2/ → Second two-in-one variant
│   ├── black-secrecy-1/        → Confidential layout with restricted fields
│   ├── blue-default-1/         → Blue-themed layout, standard extraction
│   └── blue-default-2/         → Blue-themed variant with different column mapping
│
└── timecard/          # Cartão Ponto (Timecard) variants
    ├── black-cocacola-1/       → Simple DD/MM/YYYY + 2 entry/exit times
    ├── black-cocacola-2/       → Extended Coca-Cola format with extra fields
    ├── black-horizontal-1/     → Full horizontal: DD/MM + day, skip fixed hours, folga detection
    ├── black-horizontal-2/     → Horizontal with period header (DD/MM/YYYY à DD/MM/YYYY)
    ├── black-horizontal-3/     → Horizontal variant with different header parsing
    ├── black-horizontal-4/     → Horizontal with CSV output and semicolon delimiter
    ├── black-horizontal-5/     → Extended horizontal with extra timestamp columns
    ├── black-horizontal-6/     → Horizontal with banco de horas tracking
    ├── black-pontomais/        → PontoMais: "Dia,DD/MM/YYYY" sequential format
    ├── black-secrecy-1/        → Confidential/encrypted timecard layout
    ├── blue-horizontal-1/      → Blue-themed horizontal timecard
    └── blue-horizontal-2/      → Blue-themed variant with different column order
```

## How It Works

Each `conversion.py` follows the same general pattern:

1. **Open PDF** with `pdfplumber`
2. **Extract text** (or words with coordinates for complex layouts)
3. **Detect document structure** (headers, table boundaries, date format)
4. **Parse rows** using regex patterns specific to that variant
5. **Consolidate data** across pages (handling duplicates, multi-page records)
6. **Export** to Excel (payslips) or CSV (timecards)

The key differences between variants are:
- **Column delimiters**: space, pipe (`|`), or positional (word coordinates)
- **Date formats**: `MM/YYYY`, `JAN/2025`, `DD/MM/YYYY`, `DD/MM`
- **Table markers**: "TOTAIS", "BASE/OUTROS", "Total de Vencimentos"
- **Special handling**: inverted text, duplicate pages, two-in-one layouts
