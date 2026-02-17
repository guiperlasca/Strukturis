# Timecard (Cartão Ponto) — Extraction Reference

## Overview

Timecard documents record daily clock-in/clock-out timestamps.
Each variant handles a different layout but outputs the same tabular structure.

## Common Output Fields

| Field | Description |
|-------|-------------|
| `Data` | Date of the record (DD/MM/YYYY) |
| `Entrada1` | First clock-in time (HH:MM) |
| `Saida1` | First clock-out time (HH:MM) |
| `Entrada2` | Second clock-in time (HH:MM) — after lunch break |
| `Saida2` | Second clock-out time (HH:MM) |

## Variant Details

### black-cocacola-1 (Simple Format)
- **Date format**: `DD/MM/YYYY` on each row
- **Parsing**: Extracts date, then finds 2 time pairs (entry/exit)
- **Day filter**: Skips weekends and holidays
- **Output**: CSV with semicolon (`;`) delimiter

### black-cocacola-2 (Extended Coca-Cola)
- **Same date format** as cocacola-1
- **Extra fields**: Additional columns for overtime and absences
- **Parsing**: Extended regex to capture more time slots

### black-horizontal-1 (Full Horizontal)
- **Date format**: `DD/MM` followed by day-of-week abbreviation (seg, ter, qua...)
- **Scheduled vs Actual**: First 4 times are scheduled (ignored), remaining are actual
- **Folga detection**: Keywords like "FOLGA", "(-)", "FALTA"
- **Time validation**: Only keeps strictly increasing timestamps
- **Duplicate handling**: Keeps last occurrence for same date

### black-horizontal-2 (Period Header)
- **Year extraction**: From period header `DD/MM/YYYY à DD/MM/YYYY`
- **Date format**: `DD/MM` (short) — year appended from header
- **Employee info**: Extracts name, CNPJ, department from header
- **Scheduled skip**: Ignores first 4 timestamps (predicted schedule)
- **Dash stop**: Stops reading times at dash (`-`) character

### black-horizontal-3/4/5/6 (Horizontal Variants)
- **Same core logic** as horizontal-1/2 with minor variations:
  - **3**: Different header keyword patterns
  - **4**: CSV output with configurable page range
  - **5**: Extra timestamp columns for extended shifts
  - **6**: Includes banco de horas (time bank) tracking

### black-pontomais (PontoMais Format)
- **Date format**: `Dia,DD/MM/YYYY` (e.g., "Seg,01/03/2025")
- **Sequential reading**: Times read left-to-right, stops when time decreases
- **Max 4 times**: Caps at Entrada1→Saída1→Entrada2→Saída2
- **GUI integration**: Original script includes tkinter file picker

### black-secrecy-1 (Confidential)
- **Encrypted/masked fields**: Some timestamps redacted
- **Graceful degradation**: Outputs empty strings for missing times
- **Strict validation**: Extra checks on time format validity

### blue-horizontal-1/2 (Blue-Themed)
- **Same extraction logic** as black-horizontal variants
- **Visual difference only**: Blue-themed document layout
- **Column order**: Minor variations in time column positions
