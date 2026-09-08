from app.extract.verify import collapse_ws, quote_in_page


def test_verify_quote_substring():
    page = "Revenue was 8,141 crore in FY 2023-24 on a consolidated basis."
    assert quote_in_page("8,141 crore in FY 2023-24", page)


def test_verify_quote_whitespace_collapse():
    page = "Revenue  was\n8,141   crore"
    assert quote_in_page("Revenue was 8,141 crore", page)
    assert collapse_ws("  a\n\tb  ") == "a b"


def test_verify_quote_rejects_hallucination():
    page = "Revenue was 8,141 crore in FY 2023-24."
    assert not quote_in_page("Profit was 9,999 crore in FY 2023-24.", page)


def test_verify_quote_too_short():
    assert not quote_in_page("8141", "Revenue was 8141 crore")
