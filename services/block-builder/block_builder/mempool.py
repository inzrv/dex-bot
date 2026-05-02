from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from .transaction import Transaction


@dataclass
class MempoolRecord:
    mempoolTxId: str
    transaction: Transaction
    status: str
    submittedAt: str
    chainTxHash: Optional[str] = None
    receipt: Optional[dict[str, Any]] = None
    updatedAt: Optional[str] = None

    def toJson(self) -> dict[str, Any]:
        return {
            "mempoolTxId": self.mempoolTxId,
            "transaction": self.transaction.toJson(),
            "status": self.status,
            "submittedAt": self.submittedAt,
            "chainTxHash": self.chainTxHash,
            "receipt": self.receipt,
            "updatedAt": self.updatedAt,
        }


class Mempool:
    def __init__(self) -> None:
        self._transactions: dict[str, MempoolRecord] = {}

    def addTransaction(self, transaction: Transaction) -> MempoolRecord:
        mempoolTxId = f"mp-{uuid4().hex}"

        record = MempoolRecord(
            mempoolTxId=mempoolTxId,
            transaction=transaction,
            status="pending",
            submittedAt=_local_now(),
        )
        self._transactions[mempoolTxId] = record
        return record

    def getTransaction(self, mempoolTxId: str) -> Optional[MempoolRecord]:
        return self._transactions.get(mempoolTxId)

    def markMined(
        self,
        mempoolTxId: str,
        chainTxHash: str,
        status: str,
        receipt: Optional[dict[str, Any]],
    ) -> MempoolRecord:
        record = self._transactions.get(mempoolTxId)
        if record is None:
            raise ValueError(f"transaction '{mempoolTxId}' not found")

        record.status = status
        record.chainTxHash = chainTxHash
        record.receipt = receipt
        record.updatedAt = _local_now()
        return record

    def pendingTransactions(self) -> list[MempoolRecord]:
        return [
            record
            for record in self._transactions.values()
            if record.status == "pending"
        ]


def _local_now() -> str:
    return datetime.now().astimezone().isoformat()
