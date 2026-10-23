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


# ==============================================================================
# SECTION 3: BRAZILIAN PORTUGUESE LASA (LOOK-ALIKE SOUND-ALIKE) & DOSAGE SHIELD
# ==============================================================================

def extract_dosages_pt(text: str) -> List[str]:
    """
    Extracts pharmaceutical dosage and strength specifications from Brazilian drug descriptions.
    Handles single strengths (10mg, 500mcg, 100UI, 5%), ratio strengths (10mg/ml, 50mg/2ml),
    and decimal formats with either comma or period (0,5mg or 0.5mg).
    """
    s = text.lower().replace("µg", "mcg").replace("ug", "mcg")
    pattern = r"\b(\d+(?:[.,]\d+)?)\s*(mg|mcg|g|ml|ui|%)(?:\s*/\s*(\d+(?:[.,]\d+)?)?\s*(mg|mcg|g|ml))?(?![a-zA-Z0-9])"
    dosages = []
    for m in re.finditer(pattern, s):
        num1 = m.group(1).replace(",", ".")
        try:
            val1 = float(num1)
            num1_str = f"{val1:g}"
        except ValueError:
            num1_str = num1
        unit1 = m.group(2)
        denom_num = m.group(3)
        denom_unit = m.group(4)
        if denom_unit:
            if denom_num:
                num2 = denom_num.replace(",", ".")
                try:
                    val2 = float(num2)
                    num2_str = f"{val2:g}"
                except ValueError:
                    num2_str = num2
                spec = f"{num1_str}{unit1}/{num2_str}{denom_unit}"
            else:
                spec = f"{num1_str}{unit1}/{denom_unit}"
        else:
            spec = f"{num1_str}{unit1}"
        dosages.append(spec)
    return dosages


def normalize_single_dosage(token: str) -> str:
    """
    Standardizes dosage units to prevent false negatives (e.g., '1g' vs '1000mg', '0.5g' vs '500mg').
    Normalizes mass to 'mg' and microgram variants to 'mcg'.
    """
    token = token.lower().strip()
    if "/" in token:
        parts = token.split("/", 1)
        return f"{normalize_single_dosage(parts[0])}/{normalize_single_dosage(parts[1])}"
    
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|ui|%)$", token)
    if not m:
        return token
    
    val = float(m.group(1))
    unit = m.group(2)
    
    if unit == "g":
        # Convert grams to mg: 1g -> 1000mg
        mg_val = val * 1000.0
        return f"{mg_val:g}mg"
    elif unit == "mcg" and val >= 1000.0 and (val % 1000.0 == 0):
        # Convert 1000mcg -> 1mg
        mg_val = val / 1000.0
        return f"{mg_val:g}mg"
    elif unit == "mg" and val < 1.0:
        # Convert 0.5mg -> 500mcg
        mcg_val = val * 1000.0
        return f"{mcg_val:g}mcg"
    
    return f"{val:g}{unit}"


def compare_dosages(dosages_prescribed: List[str], dosages_dispensed: List[str]) -> Tuple[bool, str]:
    """
    Compares normalized dosages between prescribed and dispensed items.
    Returns (is_match, status_code).
    """
    if not dosages_prescribed and not dosages_dispensed:
        return True, "DOSAGE_NOT_SPECIFIED"
    if not dosages_prescribed and dosages_dispensed:
        return True, "DOSAGE_SPECIFIED_ONLY_IN_DISPENSED"
    if dosages_prescribed and not dosages_dispensed:
        return False, "DOSAGE_MISSING_IN_DISPENSED"
    
    norm_p = sorted([normalize_single_dosage(d) for d in dosages_prescribed])
    norm_d = sorted([normalize_single_dosage(d) for d in dosages_dispensed])
    
    if norm_p == norm_d:
        return True, "DOSAGE_MATCH"
    else:
        return False, f"DOSAGE_MISMATCH: Prescribed {norm_p} != Dispensed {norm_d}"


def normalize_text_pt(text: str) -> str:
    """
    Camada 1: Normalizes Brazilian Portuguese drug names down to the active principle:
    - Lowercase
    - Removes accents and diacritics (ç -> c, á -> a, etc.)
    - Removes dosage, volumes, ratios, pharmaceutical forms (mg, ml, mcg, comp, inj, etc.)
    - Strips non-alphanumeric characters
    """
    s = text.lower()
    # Strip compound dosages (e.g. 10mg/ml, 500mg, 100 ui, 0,5%)
    s = re.sub(r"\b\d+([.,]\d+)?\s*(mg|mcg|µg|ug|g|ml|ui|%)(?:\s*/\s*\d*([.,]\d+)?\s*(mg|mcg|µg|ug|g|ml))?(?![a-zA-Z0-9])", " ", s)
    # Strip pharmaceutical forms and packaging labels
    s = re.sub(r"\b(comprimido|comprimidos|capsula|capsulas|injetavel|ampola|ampolas|suspensao|gotas|solucao|dragea|drageas|creme|pomada|xarope|frasco|frascos|revestido|revestidos)\w*\b", " ", s)
    
    # Decompose unicode to remove diacritics
    nfkd = unicodedata.normalize("NFD", s)
    s = "".join([c for c in nfkd if not unicodedata.combining(c)])
    
    # Keep only letters and spaces
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pt_br_phonetic_code(name: str) -> str:
    """
    Phonetic algorithm tailored specifically to Brazilian Portuguese medical nomenclature.
    Addresses typical phonetic collisions in pharmacology:
    - Silent 'H' (Hidralazina -> idralazina)
    - 'PH' -> 'F' (Morfina, Fosfato)
    - 'TH' -> 'T'
    - 'Y' -> 'I', 'W' -> 'V'
    - 'CH', 'X', 'SH' -> 'X'
    - 'C' before E/I -> 'S', 'C' elsewhere -> 'K'
    - 'Ç' -> 'S'
    - 'QU' before E/I -> 'K', 'QU' elsewhere -> 'K'
    - 'G' before E/I -> 'J', 'G' elsewhere -> 'G'
    - 'Z' at word end -> 'S' (Diazepam, etc.)
    - Intervocalic 'S' -> 'Z'
    - 'SS' -> 'S', 'RR' -> 'R'
    - Coda 'L' (end of syllable) -> 'U' (Vocalização do L caipira/brasileiro: e.g. 'Diltiazem', 'Fluconazol')
    - Coda 'M' / 'N' -> Nasalization token '~'
    """
    clean = normalize_text_pt(name)
    if not clean:
        return ""

    tokens = clean.split()
    encoded_tokens = []

    for word in tokens:
        w = word
        # 1. Archaic digraphs & silent letters
        w = re.sub(r"^h+", "", w)
        w = w.replace("ph", "f")
        w = w.replace("th", "t")
        w = w.replace("y", "i")
        w = w.replace("w", "v")
        w = w.replace("sh", "x")
        w = w.replace("ch", "x")

        # 2. 'C' and 'Ç' rules
        w = w.replace("ç", "s")
        w = re.sub(r"c(?=[ei])", "s", w)
        w = re.sub(r"c(?=[aou]|$|[^aeiou])", "k", w)

        # 3. 'QU' rules
        w = re.sub(r"qu(?=[ei])", "k", w)
        w = re.sub(r"qu", "k", w)

        # 4. 'G' rules
        w = re.sub(r"g(?=[ei])", "j", w)
        w = re.sub(r"gu(?=[ei])", "g", w)

        # 5. Intervocalic 'S' (sounds like 'Z' in PT-BR)
        vowels = "aeiou"
        w_list = list(w)
        for i in range(1, len(w_list) - 1):
            if w_list[i] == "s" and w_list[i-1] in vowels and w_list[i+1] in vowels:
                w_list[i] = "z"
        w = "".join(w_list)

        # 6. Sibilants and double consonants
        w = w.replace("ss", "s")
        w = w.replace("rr", "r")
        w = w.replace("xc", "s")
        w = w.replace("sc", "s")

        # 7. Word-final Z -> S
        if w.endswith("z"):
            w = w[:-1] + "s"

        # 8. Brazilian Portuguese L-vocalization at syllable end (e.g. Atenolol -> atenolou)
        # Any 'l' followed by a consonant or at end of word sounds like 'u'
        w = re.sub(r"l(?=$|[^aeiou])", "u", w)

        # 9. Nasalization at coda (m/n before consonant or end of word)
        w = re.sub(r"[mn](?=$|[^aeiou])", "~", w)

        # 10. Collapse duplicate adjacent consonants
        collapsed = []
        for ch in w:
            if not collapsed or ch != collapsed[-1]:
                collapsed.append(ch)
        encoded_tokens.append("".join(collapsed))

    return " ".join(encoded_tokens)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Standard dynamic programming Levenshtein distance."""
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = list(range(len(s2) + 1))
    v1 = [0] * (len(s2) + 1)

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0[:] = v1[:]

    return v0[len(s2)]


def similarity_ratio(s1: str, s2: str) -> float:
    """Normalized similarity score between 0.0 (totally different) and 1.0 (identical)."""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return max(0.0, 1.0 - (dist / max_len))


@dataclasses.dataclass(frozen=True)
class LASARiskAssessment:
    """Clinical assessment of Look-Alike Sound-Alike risk and dosage integrity."""
    drug_prescribed: str
    drug_dispensed: str
    active_ingredient_prescribed: str
    active_ingredient_dispensed: str
    active_ingredient_match: bool
    prescribed_dosages: List[str]
    dispensed_dosages: List[str]
    dosage_match: bool
    orthographic_similarity: float   # 0.0 - 1.0
    phonetic_similarity: float       # 0.0 - 1.0
    composite_risk_score: float      # Weighted composite
    risk_level: str                  # 'CRITICAL', 'WARNING', 'SAFE'
    tall_man_prescribed: str         # Highlighting differentiating characters
    tall_man_dispensed: str
    recommendation: str

    def to_dict(self) -> Dict[str, Union[str, float, bool, List[str]]]:
        return {
            "drug_prescribed": self.drug_prescribed,
            "drug_dispensed": self.drug_dispensed,
            "active_ingredient_prescribed": self.active_ingredient_prescribed,
            "active_ingredient_dispensed": self.active_ingredient_dispensed,
            "active_ingredient_match": self.active_ingredient_match,
            "prescribed_dosages": self.prescribed_dosages,
            "dispensed_dosages": self.dispensed_dosages,
            "dosage_match": self.dosage_match,
            "orthographic_similarity": round(self.orthographic_similarity, 3),
            "phonetic_similarity": round(self.phonetic_similarity, 3),
            "composite_risk_score": round(self.composite_risk_score, 3),
            "risk_level": self.risk_level,
            "tall_man_prescribed": self.tall_man_prescribed,
            "tall_man_dispensed": self.tall_man_dispensed,
            "recommendation": self.recommendation
        }


# Curated ISMP Brasil / ANVISA official Tall Man Lettering catalog for high-risk pairs
ISMP_TALL_MAN_DICTIONARY: Dict[str, str] = {
    "clorpromazina": "clorproMAZINA",
    "clomipramina": "clomiPRAMINA",
    "ceftriaxona": "cefTRIAXONA",
    "cefazolina": "cefAZOLINA",
    "cefotaxima": "cefoTAXIMA",
    "doxorrubicina": "DOXOrrubicina",
    "daunorrubicina": "DAUNOrrubicina",
    "hidralazina": "HIDRAlazina",
    "hidroxizina": "hidroxiZINA",
    "metformina": "metFORMINA",
    "metronidazol": "metroNIDAZOL",
    "fluoxetina": "fluOXETINA",
    "fluvoxamina": "fluVOXAMINA",
    "tramadol": "TRAmadol",
    "trazodona": "TRAZOdona",
    "diazepam": "diazePAM",
    "diltiazem": "dilTIAZEM",
    "levotiroxina": "levoTIROXINA",
    "levofloxacino": "levoFLOXACINO",
    "omeprazol": "omePRAZOL",
    "pantoprazol": "pantoPRAZOL",
    "enalapril": "enalaPRIL",
    "ramipril": "ramiPRIL",
    "insulina regular": "insulina REGULAR",
    "insulina nph": "insulina NPH",
}


def generate_tall_man_pair(name1: str, name2: str) -> Tuple[str, str]:
    """
    Generates ISMP Brasil / ANVISA Tall Man Lettering for two colliding medication names.
    Prioritizes the official ISMP Brasil standardized catalog. If not found in the catalog,
    dynamically computes distinctive character sequences on the normalized generic names
    and capitalizes the differentiating middle or suffix/prefix.
    """
    clean1 = normalize_text_pt(name1)
    clean2 = normalize_text_pt(name2)

    # 1. Official ISMP Catalog lookup
    t1 = ISMP_TALL_MAN_DICTIONARY.get(clean1)
    t2 = ISMP_TALL_MAN_DICTIONARY.get(clean2)
    if t1 and t2:
        return t1, t2
    elif t1 and not t2:
        return t1, name2
    elif t2 and not t1:
        return name1, t2

    # 2. Dynamic Algorithmic Fallback
    n1 = clean1
    n2 = clean2

    p = 0
    while p < len(n1) and p < len(n2) and n1[p] == n2[p]:
        p += 1

    s = 0
    while s < (len(n1) - p) and s < (len(n2) - p) and n1[-(s + 1)] == n2[-(s + 1)]:
        s += 1

    mid1 = n1[p : len(n1) - s] if s > 0 else n1[p:]
    mid2 = n2[p : len(n2) - s] if s > 0 else n2[p:]

    prefix = n1[:p]
    suffix = n1[len(n1) - s:] if s > 0 else ""

    tall1 = f"{prefix}{mid1.upper()}{suffix}"
    tall2 = f"{prefix}{mid2.upper()}{suffix}"

    return tall1, tall2


# Curated high-risk ANVISA / ISMP Brasil known LASA collision catalog
KNOWN_BRAZILIAN_LASA_PAIRS = [
    ("clorpromazina", "clomipramina"),
    ("ceftriaxona", "cefazolina"),
    ("cefotaxima", "cefazolina"),
    ("doxorrubicina", "daunorrubicina"),
    ("hidralazina", "hidroxizina"),
    ("metformina", "metronidazol"),
    ("fluoxetina", "fluvoxamina"),
    ("tramadol", "trazodona"),
    ("diazepam", "diltiazem"),
    ("levotiroxina", "levofloxacino"),
    ("omeprazol", "pantoprazol"),
    ("enalapril", "ramipril"),
    ("insulina regular", "insulina nph"),
]


class LASACollisionDetector:
    """
    Shield against medical dispensing errors caused by phonetic and orthographic
    confusion in Brazilian Portuguese healthcare settings.
    """
    def __init__(self, custom_catalog: Optional[List[Tuple[str, str]]] = None):
        self.known_pairs = set()
        for a, b in (custom_catalog or KNOWN_BRAZILIAN_LASA_PAIRS):
            norm_a = normalize_text_pt(a)
            norm_b = normalize_text_pt(b)
            self.known_pairs.add(tuple(sorted((norm_a, norm_b))))

    def assess_collision(self, prescribed_name: str, candidate_name: str) -> LASARiskAssessment:
        # Camada 1: Normalização do Princípio Ativo
        norm_prescribed = normalize_text_pt(prescribed_name)
        norm_candidate = normalize_text_pt(candidate_name)
        active_match = (norm_prescribed == norm_candidate)

        # Camada 2: Extração e Comparação de Dosagem / Posologia
        dosages_prescribed = [normalize_single_dosage(d) for d in extract_dosages_pt(prescribed_name)]
        dosages_dispensed = [normalize_single_dosage(d) for d in extract_dosages_pt(candidate_name)]
        dosage_match, dosage_status = compare_dosages(dosages_prescribed, dosages_dispensed)

        # Caso 1: Princípios Ativos Idênticos
        if active_match:
            if not dosage_match:
                # CAMADA 2 CRÍTICA: Mesma substância, dosagem/concentração incompatível
                dose_p_str = ", ".join(dosages_prescribed) if dosages_prescribed else "Não especificada"
                dose_d_str = ", ".join(dosages_dispensed) if dosages_dispensed else "Não especificada"
                return LASARiskAssessment(
                    drug_prescribed=prescribed_name,
                    drug_dispensed=candidate_name,
                    active_ingredient_prescribed=norm_prescribed,
                    active_ingredient_dispensed=norm_candidate,
                    active_ingredient_match=True,
                    prescribed_dosages=dosages_prescribed,
                    dispensed_dosages=dosages_dispensed,
                    dosage_match=False,
                    orthographic_similarity=1.0,
                    phonetic_similarity=1.0,
                    composite_risk_score=1.0,
                    risk_level="CRITICAL",
                    tall_man_prescribed=f"{prescribed_name} [DOSE: {dose_p_str}]",
                    tall_man_dispensed=f"{candidate_name} [DIVERGENTE: {dose_d_str}]",
                    recommendation=f"BLOQUEIO POSOLÓGICO CRÍTICO: Princípio ativo '{norm_prescribed.upper()}' idêntico, mas dosagem/concentração incompatível ({dose_p_str} vs {dose_d_str}). Risco fatal de intoxicação ou subdose!"
                )
            else:
                # Princípio ativo e dosagem correspondem perfeitamente
                return LASARiskAssessment(
                    drug_prescribed=prescribed_name,
                    drug_dispensed=candidate_name,
                    active_ingredient_prescribed=norm_prescribed,
                    active_ingredient_dispensed=norm_candidate,
                    active_ingredient_match=True,
                    prescribed_dosages=dosages_prescribed,
                    dispensed_dosages=dosages_dispensed,
                    dosage_match=True,
                    orthographic_similarity=1.0,
                    phonetic_similarity=1.0,
                    composite_risk_score=0.0,
                    risk_level="SAFE",
                    tall_man_prescribed=prescribed_name,
                    tall_man_dispensed=candidate_name,
                    recommendation="Medicamento e dosagem correspondem exatamente ao prescrito."
                )

        # Caso 2: Princípios Ativos Diferentes (Avaliação LASA Fonética e Ortográfica)
        ortho_sim = similarity_ratio(norm_prescribed, norm_candidate)
        phone_prescribed = pt_br_phonetic_code(prescribed_name)
        phone_candidate = pt_br_phonetic_code(candidate_name)
        phone_sim = similarity_ratio(phone_prescribed, phone_candidate)

        pair_key = tuple(sorted((norm_prescribed, norm_candidate)))
        is_known_lasa = pair_key in self.known_pairs

        composite = (0.55 * phone_sim) + (0.45 * ortho_sim)

        if is_known_lasa:
            composite = max(composite, 0.88)
            risk_level = "CRITICAL"
            rec = "ALERTA MÁXIMO (ISMP/ANVISA): Medicamento com alto índice de colisão fatal registrado."
        elif composite >= 0.72 or (phone_sim >= 0.80 and ortho_sim >= 0.60):
            risk_level = "CRITICAL"
            rec = "BLOQUEIO CLÍNICO RECOMENDADO: Alta probabilidade de confusão LASA (troca inadvertida de substância)."
        elif composite >= 0.58:
            risk_level = "WARNING"
            rec = "ATENÇÃO: Semelhança ortográfica/fonética moderada. Confirmar prescrição e indicação."
        else:
            risk_level = "SAFE"
            rec = "Risco de confusão LASA insignificante."

        tall1, tall2 = generate_tall_man_pair(prescribed_name, candidate_name)

        return LASARiskAssessment(
            drug_prescribed=prescribed_name,
            drug_dispensed=candidate_name,
            active_ingredient_prescribed=norm_prescribed,
            active_ingredient_dispensed=norm_candidate,
            active_ingredient_match=False,
            prescribed_dosages=dosages_prescribed,
            dispensed_dosages=dosages_dispensed,
            dosage_match=dosage_match,
            orthographic_similarity=ortho_sim,
            phonetic_similarity=phone_sim,
            composite_risk_score=composite,
            risk_level=risk_level,
            tall_man_prescribed=tall1,
            tall_man_dispensed=tall2,
            recommendation=rec
        )


