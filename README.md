# Angela Practical Funding Toolkit

This repo replaces the fake "quantum grant" code with practical local tools.

It does not guarantee money, file legal claims, or appraise collectibles. It helps you organize real opportunities, evidence, and comparable sale data so you can take the next useful step.

## Quick Start

Run these from PowerShell:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
```

The scripts write results into the `output` folder.

## Files

- `grants.py` ranks grant/scholarship/emergency aid opportunities from `data/grants.csv`.
- `housing_violations.py` summarizes unresolved housing issues from `data/housing_violations.csv`.
- `shell_catalog.py` estimates collectible ranges only from comparable sale values you provide in `data/shell_items.csv`.

## How To Use For Real

1. Open the CSV files in `data`.
2. Replace the sample rows with real opportunities, violations, or items.
3. Run the matching script.
4. Use the generated files in `output` as your call list, application tracker, or evidence packet.

## Important Limits

- No script can guarantee a grant, settlement, or sale price.
- Do not send private documents to random websites.
- For legal action, use the housing summary as an organizer and talk to a qualified tenant/legal aid office.

