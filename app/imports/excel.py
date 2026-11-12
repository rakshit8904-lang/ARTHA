from datetime import date, datetime
from io import BytesIO
from zipfile import ZipFile

from openpyxl import load_workbook

from app.errors import InvalidRequest
from app.imports.csv_parser import ImportFileError, parse_records


class ChooseSheet(InvalidRequest):
    code = "choose_sheet"


def records(sheet, max_rows):
    # Ignore producer-supplied sheet dimensions, which can hide data or inflate empty space.
    sheet.reset_dimensions()
    width = 0
    for number, cells in enumerate(sheet.iter_rows(), 1):
        if number > max_rows + 1 or len(cells) > 256:
            raise ImportFileError("Worksheet exceeds the supported row or column limit")
        values = []
        for cell in cells:
            if cell.data_type in ("f", "e"):
                raise ImportFileError("Use values instead of formulas or Excel errors on the selected sheet")
            value = cell.value
            if isinstance(value, datetime):
                value = value.date()
            if isinstance(value, date):
                value = value.isoformat()
            values.append("" if value is None else str(value))
        while values and not values[-1]:
            values.pop()
        if number == 1:
            width = len(values)
        yield values + [""] * max(0, width - len(values))


def read_sheet(data, selected, preset, overrides, max_rows):
    # XLSX is a ZIP archive. Bound decompression before opening any XML.
    try:
        with ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(e.file_size for e in entries) > 24 * 1024 * 1024:
                raise ImportFileError("Workbook is too large when expanded")
        book = load_workbook(BytesIO(data), read_only=True, data_only=False, keep_links=False)
        try:
            names = [sheet.title for sheet in book.worksheets if sheet.sheet_state == "visible"]
            if not names:
                raise ImportFileError("Workbook has no visible worksheets")
            if selected is None and len(names) > 1:
                raise ChooseSheet("Choose one worksheet to review.", details={"sheets": names})
            name = names[0] if selected is None else selected
            if name not in names:
                raise ImportFileError("Choose a visible worksheet from this workbook")
            return name, parse_records(records(book[name], max_rows), preset, overrides, max_rows)
        finally:
            book.close()
    except (ChooseSheet, ImportFileError):
        raise
    except Exception as exc:
        raise ImportFileError("Could not read this Excel workbook. Use an unencrypted .xlsx file.") from exc
