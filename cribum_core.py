"""
Cribum Mobile: Escudo Clínico e Antifraude do SUS
Core Cryptographic, Regulatory, and Clinical Safety Engine

Components:
1. GS1 DataMatrix Parser (ANVISA SNCM / RDC 319 / RDC 157 Compliant)
2. RFC 6962 Compliant Merkle Tree (Append-only Cryptographic Dispensing Log)
3. Brazilian Portuguese LASA (Look-Alike Sound-Alike) Collision Detector & Tall Man Generator

Author: André Rogério da Silva Filho
Campus Mobile 15 - Categoria: Saúde e Tecnologias Assistivas
"""

from __future__ import annotations
import dataclasses
import datetime
import hashlib
import json
import math
import re
import unicodedata
from typing import Dict, List, Optional, Set, Tuple, Union


# ==============================================================================
# SECTION 1: GS1 DATAMATRIX PARSER (ANVISA SNCM / RDC 319)
# ==============================================================================

GS_CHAR = "\x1d"  # ASCII 29 Group Separator (FNC1 representation in raw barcode)


@dataclasses.dataclass(frozen=True)
class GS1Medication:
    """Represents a scanned medication package verified through GS1 DataMatrix."""
    gtin: str                  # AI (01) - 14 digits
    serial_number: str         # AI (21) - Up to 20 alphanumeric characters
    expiration_date: datetime.date  # AI (17) - YYMMDD
    batch_lot: str             # AI (10) - Up to 20 alphanumeric characters
    raw_code: str              # Original unscrambled payload

    @property
    def canonical_id(self) -> str:
        """Global unique identifier for this individual package unit."""
        return f"{self.gtin}:{self.serial_number}"

    def is_expired(self, as_of: Optional[datetime.date] = None) -> bool:
        """Checks if package is past its expiration date."""
        ref_date = as_of or datetime.date.today()
        return self.expiration_date < ref_date

    def to_dict(self) -> Dict[str, str]:
        return {
            "gtin": self.gtin,
            "serial_number": self.serial_number,
            "expiration_date": self.expiration_date.isoformat(),
            "batch_lot": self.batch_lot,
            "canonical_id": self.canonical_id,
            "is_expired": str(self.is_expired())
        }


class GS1ParseError(ValueError):
    """Raised when GS1 DataMatrix string fails syntax or semantic validation."""
    pass


def validate_gtin14_check_digit(gtin: str) -> bool:
    """Validates GS1 Modulo 10 check digit for GTIN-14."""
    if not (isinstance(gtin, str) and len(gtin) == 14 and gtin.isdigit()):
        return False
    digits = [int(c) for c in gtin]
    # In GTIN-14, weights alternate 3, 1, 3, 1... for the first 13 digits
    # (position 1 has weight 3, position 2 weight 1, ..., position 13 weight 3)
    weighted_sum = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits[:13]))
    expected_check = (10 - (weighted_sum % 10)) % 10
    return digits[13] == expected_check


def parse_gs1_date(yymmdd: str) -> datetime.date:
    """
    Parses GS1 AI (17) expiration date.
    Per GS1 specification:
    - If day is '00', it signifies the last calendar day of the month.
    - YY rollover: years 00-49 map to 2000-2049, 50-99 map to 1950-1999 (typically 2000s for drugs).
    """
    if len(yymmdd) != 6 or not yymmdd.isdigit():
        raise GS1ParseError(f"Invalid GS1 date format: '{yymmdd}', expected 6 digits YYMMDD")
    
    yy = int(yymmdd[0:2])
    mm = int(yymmdd[2:4])
    dd = int(yymmdd[4:6])

    if mm < 1 or mm > 12:
        raise GS1ParseError(f"Invalid month in GS1 date: {mm}")

    year = 2000 + yy if yy < 70 else 1900 + yy

    # GS1 rule: day '00' indicates last day of month
    if dd == 0:
        if mm in (1, 3, 5, 7, 8, 10, 12):
            dd = 31
        elif mm in (4, 6, 9, 11):
            dd = 30
        elif mm == 2:
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            dd = 29 if is_leap else 28
    else:
        # Validate day range
        if dd < 1 or dd > 31:
            raise GS1ParseError(f"Invalid day in GS1 date: {dd}")

    try:
        return datetime.date(year, mm, dd)
    except ValueError as e:
        raise GS1ParseError(f"Invalid calendar date YYMMDD '{yymmdd}': {e}")


def parse_gs1_datamatrix(raw_payload: str) -> GS1Medication:
    """
    Parses ANVISA SNCM compliant GS1 DataMatrix 2D barcodes.
    Supports:
    1. Human Readable / Bracketed format:
       e.g., '(01)07891234567890(21)SER12345(17)281231(10)LOT998'
    2. Raw GS-separated or plain element strings:
       e.g., '010789123456789021SER12345\x1d1728123110LOT998'
       or '<GS>' textual delimiter placeholders.
    """
    cleaned = raw_payload.strip()
    if not cleaned:
        raise GS1ParseError("Empty GS1 DataMatrix barcode string")

    # Replace visual '<GS>' representation with actual GS char
    cleaned = cleaned.replace("<GS>", GS_CHAR)

    gtin: Optional[str] = None
    serial: Optional[str] = None
    expiry_str: Optional[str] = None
    batch: Optional[str] = None

    # Format 1: Bracketed representation '(AI)Value'
    if cleaned.startswith("(") and ")" in cleaned:
        matches = re.findall(r"\((\d{2,4})\)([^()]+)", cleaned)
        for ai, val in matches:
            val_clean = val.strip()
            if ai == "01":
                gtin = val_clean
            elif ai == "21":
                serial = val_clean
            elif ai == "17":
                expiry_str = val_clean
            elif ai == "10":
                batch = val_clean
    else:
        # Format 2: Raw element string parser with FNC1 / GS separators
        # Fixed length AIs: 01 (14 digits), 17 (6 digits)
        # Variable length AIs: 21 (up to 20 chars), 10 (up to 20 chars)
        i = 0
        n = len(cleaned)
        while i < n:
            # Skip any stray GS characters
            while i < n and cleaned[i] == GS_CHAR:
                i += 1
            if i >= n:
                break

            ai_2 = cleaned[i:i+2]
            if ai_2 == "01":
                # Fixed 14 chars
                val = cleaned[i+2:i+16]
                if len(val) < 14:
                    raise GS1ParseError(f"Truncated GTIN under AI 01: '{val}'")
                gtin = val
                i += 16
            elif ai_2 == "17":
                # Fixed 6 chars
                val = cleaned[i+2:i+8]
                if len(val) < 6:
                    raise GS1ParseError(f"Truncated expiry under AI 17: '{val}'")
                expiry_str = val
                i += 8
            elif ai_2 in ("21", "10"):
                # Variable length up to 20 chars terminated by GS or end-of-string
                start_val = i + 2
                gs_idx = cleaned.find(GS_CHAR, start_val)
                if gs_idx == -1:
                    # No GS found; could run to the end of string or look ahead for known next fixed AI
                    # In real ANVISA scans without GS, variable fields often take remaining string or are at end
                    val = cleaned[start_val:]
                    i = n
                else:
                    val = cleaned[start_val:gs_idx]
                    i = gs_idx + 1
                
                if ai_2 == "21":
                    serial = val
                else:
                    batch = val
            else:
                # Unknown AI or unsynchronized stream
                raise GS1ParseError(f"Unsupported or unrecognized GS1 AI at position {i}: '{cleaned[i:i+4]}'")

    # Validate mandatory ANVISA fields (RDC 319 / SNCM)
    missing = []
    if not gtin: missing.append("GTIN (AI 01)")
    if not serial: missing.append("Serial (AI 21)")
    if not expiry_str: missing.append("Data de Validade (AI 17)")
    if not batch: missing.append("Lote (AI 10)")
    if missing:
        raise GS1ParseError(f"Barcode is missing mandatory ANVISA SNCM fields: {', '.join(missing)}")

    # Sanity checks
    if not validate_gtin14_check_digit(gtin):
        raise GS1ParseError(f"Invalid GTIN-14 check digit: '{gtin}'")

    parsed_expiry = parse_gs1_date(expiry_str)

    return GS1Medication(
        gtin=gtin,
        serial_number=serial,
        expiration_date=parsed_expiry,
        batch_lot=batch,
        raw_code=raw_payload
    )


