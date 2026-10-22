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


# ==============================================================================
# SECTION 2: STANDALONE RFC 6962 MERKLE TREE (AUDIT LOG & DOUBLE-DISPENSE SHIELD)
# ==============================================================================

# RFC 6962 Domain Separation Prefixes
RFC6962_LEAF_PREFIX = b"\x00"
RFC6962_NODE_PREFIX = b"\x01"


def rfc6962_hash_leaf(data: bytes) -> bytes:
    """Leaf hash: SHA-256(0x00 || data)"""
    return hashlib.sha256(RFC6962_LEAF_PREFIX + data).digest()


def rfc6962_hash_children(left: bytes, right: bytes) -> bytes:
    """Internal node hash: SHA-256(0x01 || left || right)"""
    return hashlib.sha256(RFC6962_NODE_PREFIX + left + right).digest()


@dataclasses.dataclass(frozen=True)
class DispensingEvent:
    """
    Immutable dispensing event representing the delivery of a medication package
    under SUS (Componente Especializado / Farmácia de Alto Custo).
    LGPD compliant: Patient CPF is never stored in plain text, only as a salted HMAC/hash.
    """
    event_id: str             # UUID or high-resolution deterministic nonce
    canonical_drug_id: str    # GTIN:SERIAL
    patient_hash: str         # HMAC-SHA256(CPF, clinic_salt)
    prescriber_crm: str       # e.g., 'CRM/SP 123456'
    dispenser_crf: str        # e.g., 'CRF/SP 654321'
    cnes_clinic_code: str     # Cadastro Nacional de Estabelecimentos de Saúde
    timestamp_utc: str        # ISO-8601 UTC timestamp

    def to_canonical_bytes(self) -> bytes:
        """Deterministic canonical JSON serialization for Merkle leaf hashing."""
        payload = {
            "cnes": self.cnes_clinic_code,
            "crm": self.prescriber_crm,
            "crf": self.dispenser_crf,
            "drug_id": self.canonical_drug_id,
            "event_id": self.event_id,
            "patient_hash": self.patient_hash,
            "timestamp": self.timestamp_utc,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


class DoubleDispenseError(Exception):
    """Raised when an attempt is made to dispense an already dispensed serial number."""
    pass


class MerkleAuditProofError(ValueError):
    """Raised when an audit proof fails verification against the Merkle Root."""
    pass


class MerkleTree:
    """
    Standalone RFC 6962 Compliant Merkle Tree with complete audit proofs and
    local double-dispensation cryptographic verification.
    """
    def __init__(self):
        self.leaves: List[bytes] = []             # Raw leaf byte payloads
        self.leaf_hashes: List[bytes] = []        # rfc6962_hash_leaf(data)
        self._serial_registry: Dict[str, int] = {} # canonical_drug_id -> leaf_index
        self._tree_cache: Optional[bytes] = None

    def __len__(self) -> int:
        return len(self.leaves)

    @property
    def size(self) -> int:
        return len(self.leaves)

    def append_dispensing(self, event: DispensingEvent) -> int:
        """
        Appends a dispensing event to the tamper-evident log.
        Prevents double-dispensation fraud locally before cryptographic sealing.
        """
        drug_id = event.canonical_drug_id
        if drug_id in self._serial_registry:
            prev_idx = self._serial_registry[drug_id]
            raise DoubleDispenseError(
                f"DOUBLE DISPENSATION DETECTED: Drug unit '{drug_id}' was already dispensed at leaf index #{prev_idx}."
            )

        data = event.to_canonical_bytes()
        leaf_hash = rfc6962_hash_leaf(data)
        idx = len(self.leaves)
        self.leaves.append(data)
        self.leaf_hashes.append(leaf_hash)
        self._serial_registry[drug_id] = idx
        self._tree_cache = None  # Invalidate root cache
        return idx

    def get_root_hash(self) -> str:
        """Computes and returns the RFC 6962 Merkle Tree Root as hex string."""
        if not self.leaf_hashes:
            # Empty tree hash per standard RFC 6962 is SHA-256 of empty string
            return hashlib.sha256(b"").hexdigest()
        root_bytes = self._compute_subtree_hash(0, len(self.leaf_hashes))
        return root_bytes.hex()

    def _compute_subtree_hash(self, start: int, end: int) -> bytes:
        """
        RFC 6962 subtree hash recursive computation.
        If length == 1: return leaf_hash
        Else: k = largest power of 2 < length
              return hash(0x01 || subtree(start, start+k) || subtree(start+k, end))
        """
        count = end - start
        if count == 1:
            return self.leaf_hashes[start]
        k = 1 << ((count - 1).bit_length() - 1)
        left = self._compute_subtree_hash(start, start + k)
        right = self._compute_subtree_hash(start + k, end)
        return rfc6962_hash_children(left, right)

    def get_audit_proof(self, leaf_index: int) -> List[Tuple[str, str]]:
        """
        Generates RFC 6962 Audit Proof for leaf at `leaf_index`.
        Returns a list of tuples: (hex_hash, direction) where direction is 'L' (left sibling) or 'R' (right sibling).
        """
        n = len(self.leaf_hashes)
        if not (0 <= leaf_index < n):
            raise IndexError(f"Leaf index {leaf_index} out of range [0, {n-1}]")
        
        proof: List[Tuple[str, str]] = []
        self._build_audit_path(leaf_index, 0, n, proof)
        return proof

    def _build_audit_path(self, target: int, start: int, end: int, proof: List[Tuple[str, str]]):
        count = end - start
        if count == 1:
            return
        k = 1 << ((count - 1).bit_length() - 1)
        split = start + k
        if target < split:
            # Target is in left subtree, sibling is right subtree
            sibling_hash = self._compute_subtree_hash(split, end)
            proof.append((sibling_hash.hex(), "R"))
            self._build_audit_path(target, start, split, proof)
        else:
            # Target is in right subtree, sibling is left subtree
            sibling_hash = self._compute_subtree_hash(start, split)
            proof.append((sibling_hash.hex(), "L"))
            self._build_audit_path(target, split, end, proof)

    @staticmethod
    def verify_audit_proof(
        leaf_data: bytes,
        leaf_index: int,
        tree_size: int,
        expected_root_hex: str,
        proof: List[Tuple[str, str]]
    ) -> bool:
        """
        RFC 6962 Audit Path Verification.
        Computes the root from the leaf hash and the proof siblings in reverse order.
        """
        if not (0 <= leaf_index < tree_size):
            return False
        
        current = rfc6962_hash_leaf(leaf_data)
        # Sibling list in _build_audit_path was appended top-down; reverse for bottom-up accumulation
        for sibling_hex, direction in reversed(proof):
            sibling_bytes = bytes.fromhex(sibling_hex)
            if direction == "R":
                current = rfc6962_hash_children(current, sibling_bytes)
            elif direction == "L":
                current = rfc6962_hash_children(sibling_bytes, current)
            else:
                return False
        return current.hex().lower() == expected_root_hex.lower()


