import hashlib
from typing import Any, Dict, List


class RelatorAgent:
    """
    Agente Relator Pericial & Custódia Criptográfica (RFC 6962 / Merkle Chain):
    Consolida evidências visuais ancoradas, apontamentos normativos e deliberações
    humanas (HITL) em uma cadeia de custódia encadeada por SHA-256.
    """

    @staticmethod
    def compute_chain_hash(
        prev_chain_hash: str,
        content_hash: str,
        run_id: str,
        actor_id: str,
        action: str,
        confirmed_value: str,
        reason: str,
    ) -> str:
        payload = (
            f"{prev_chain_hash}|{content_hash}|{run_id}|"
            f"{actor_id}|{action}|{confirmed_value}|{reason}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def verify_audit_chain(cls, events: List[Dict[str, Any]], content_hash: str) -> bool:
        prev = "0" * 64
        for ev in events:
            expected = cls.compute_chain_hash(
                prev_chain_hash=prev,
                content_hash=content_hash,
                run_id=str(ev.get("run_id") or ""),
                actor_id=str(ev.get("actor_id") or ""),
                action=str(ev.get("action") or ""),
                confirmed_value=str(ev.get("confirmed_value") or ""),
                reason=str(ev.get("reason") or ""),
            )
            if ev.get("chain_hash") and ev["chain_hash"] != expected:
                return False
            prev = ev.get("chain_hash") or expected
        return True
