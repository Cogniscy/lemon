from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


PACK_DIR = Path("annotation/linguist_review_pack")
XLSX_PATH = PACK_DIR / "expert_validation_form.xlsx"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def test_linguist_review_pack_files_exist():
    assert XLSX_PATH.exists()
    assert (PACK_DIR / "README.md").exists()
    assert (PACK_DIR / "FIELD_GUIDE.md").exists()
    assert (PACK_DIR / "RETURN_FORMAT.md").exists()

    readme = (PACK_DIR / "README.md").read_text(encoding="utf-8")
    assert "expert_validation_form.xlsx" in readme
    assert "yellow columns" in readme
    assert "2–3 day" in readme

    guide = (PACK_DIR / "FIELD_GUIDE.md").read_text(encoding="utf-8")
    assert "verdict" in guide
    assert "direction_or_role_ok" in guide
    assert "polarity_ok" in guide


def test_linguist_excel_workbook_structure():
    with ZipFile(XLSX_PATH) as archive:
        names = set(archive.namelist())
        assert "xl/workbook.xml" in names
        assert "xl/worksheets/sheet1.xml" in names

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet_names = [sheet.attrib["name"] for sheet in workbook.findall(".//x:sheet", NS)]
        assert sheet_names == ["Review", "Instructions", "Legend", "Summary"]

        review = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = review.findall(".//x:row", NS)
        assert len(rows) == 51  # header + 50 review rows

        cols = review.findall(".//x:col", NS)
        assert len(cols) >= 14
        # Ensure text-heavy columns are widened rather than collapsed.
        widths = {int(col.attrib["min"]): float(col.attrib["width"]) for col in cols}
        assert widths[5] >= 40  # example_triple
        assert widths[6] >= 45  # example_text
        assert widths[7] >= 40  # proposed_factors

        validations = review.findall(".//x:dataValidation", NS)
        sqrefs = {validation.attrib.get("sqref") for validation in validations}
        assert {"H2:H51", "K2:K51", "L2:L51"}.issubset(sqrefs)


def test_linguist_excel_pack_is_linked_from_docs():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "annotation/linguist_review_pack/" in readme
    assert "expert_validation_form.xlsx" in readme

    roadmap = Path("docs/ROADMAP.md").read_text(encoding="utf-8")
    assert "lem23-linguist-excel-pack" in roadmap
    assert "annotation/linguist_review_pack/" in roadmap

    audit = Path("docs/CLAIMS_AND_METRICS_AUDIT.md").read_text(encoding="utf-8")
    assert "expert_validation_form.xlsx" in audit
