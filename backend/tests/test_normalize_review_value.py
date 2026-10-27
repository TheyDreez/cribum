import unicodedata
import pytest

from backend.api.app import normalize_review_value


@pytest.mark.parametrize(
    "input_val,expected",
    [
        # Standard string normalization & lowercasing
        ("Losartana 50mg", "losartana 50mg"),
        ("LOSARTANA 50MG", "losartana 50mg"),
        ("  Losartana   50mg  ", "losartana 50mg"),

        # Whitespace handling (tabs, newlines, multiple spaces)
        ("Losartana\t\n  50mg \r\n 1x ao dia", "losartana 50mg 1x ao dia"),
        ("", ""),
        ("   \t\n  ", ""),

        # Unicode NFKC normalization - Fullwidth characters
        ("Ｌｏｓａｒｔａｎａ ５０ｍｇ", "losartana 50mg"),

        # Unicode NFKC normalization - Ligatures
        ("ﬁle", "file"),  # U+FB01 Latin Small Ligature fi

        # Unicode NFKC normalization - Compatibility characters
        ("50mg/m²", "50mg/m2"),

        # Accented characters & decomposed Unicode (NFD -> NFKC)
        ("Solução", "solução"),
        (unicodedata.normalize("NFD", "Solução"), "solução"),

        # Casefolding edge cases (e.g. German Eszett 'ß' casefolds to 'ss')
        ("STRAßE", "strasse"),
        ("GROß", "gross"),
    ],
)
def test_normalize_review_value_scenarios(input_val: str, expected: str):
    assert normalize_review_value(input_val) == expected


def test_normalize_review_value_identity_and_determinism():
    text = "  Dipirona  500mg \n  Solução  "
    first_pass = normalize_review_value(text)
    second_pass = normalize_review_value(first_pass)
    assert first_pass == second_pass
    assert first_pass == "dipirona 500mg solução"
