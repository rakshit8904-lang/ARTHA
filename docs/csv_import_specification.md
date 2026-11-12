# CSV import specification (parser csv-v1)

Excel workbooks (`.xlsx`, parser `xlsx-v1`) use the same column headings and approval process described below. Put headings in the first row of a visible worksheet. Upload one worksheet at a time. Excel date cells and numeric amounts are supported. Use values for calculated cells before uploading. A workbook with several visible sheets prompts for a selection before any rows are saved. Uploading the same workbook and sheet twice returns its existing import. Each different sheet can be reviewed separately. The app discards the uploaded workbook after parsing.

Limits (configurable): file size 2 MB (`MAX_UPLOAD_BYTES`), 5,000 data rows (`MAX_IMPORT_ROWS`), description 500 characters. Extension must be `.csv`. Comma delimiter. UTF-8 (with or without BOM); cp1252 is accepted as a fallback. Files containing NUL bytes are rejected. Uploaded content is only parsed as data, never executed; the filename is reduced to its base name.

Header names are case-insensitive. Two layouts, chosen at upload:

**signed_amount** (default): required `date`, `description`, `amount`; optional `direction`, `currency`, `type`, `category`.
- Without a `direction` column: positive amount = credit (money in), negative = debit (money out).
- With a `direction` column (`credit`/`debit`/`cr`/`dr`): the amount must be positive.

**debit_credit**: required `date`, `description`, `debit`, `credit`; optional `currency`, `type`, `category`. Exactly one of debit/credit must be filled.

Any header name can be overridden through the API/service (`overrides`, e.g. `{"description": "Narration"}`). The web form currently offers only the two layouts above.

Dates: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `DD-Mon-YYYY`, `DD Mon YYYY` (day first; years 2000-2100). Amounts: digits with optional commas, up to 2 decimals, optional `INR`/`Rs`/rupee prefix, parentheses or `-` for negative; zero, exponent notation, NaN and interior spaces are rejected. Currency: blank or `INR` only.

`type` (optional) must be one of the nine ledger types; `category` (optional) one of the 13 labels. For a row without a type, choose a type before standard approval or explicitly use **Approve & review later**. The latter saves the recognized movement in the ledger with its classification open. Income and refunds must be credits; purchases, fees, loan payments and cash withdrawals must be debits.

Row problems never drop the row: it is staged as *invalid* with row-level messages, and can be edited or rejected. File-level problems (missing required column, empty file, binary data, malformed quoting, too many rows) reject the file and are recorded in import history as *failed*.

Idempotency: the same file (SHA-256) to the same account again returns the existing import and adds nothing. Overlapping statements: a row is flagged *possible duplicate* when the account already has a matching approved row (or a pending row from another import) with the same date, amount, direction and normalized description; matching counts occurrences, so a second identical coffee is flagged only if two already exist. Repeats within one file are never flagged. Flagged rows need explicit confirmation to approve.

Status labels: pending, invalid, approved, rejected. Row numbers are file record numbers; the header is row 1.
