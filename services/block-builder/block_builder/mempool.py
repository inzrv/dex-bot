from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .transaction import Transaction


@dataclass
class MempoolRecord:
    transaction: Transaction
    status: str
    submittedAt: str

    def toJson(self) -> dict[str, Any]:
        return {
            "transaction": self.transaction.toJson(),
            "status": self.status,
            "submittedAt": self.submittedAt,
        }


class Mempool:
    def __init__(self) -> None:
        self._transactions: dict[str, MempoolRecord] = {}

    def addTransaction(self, transaction: Transaction) -> MempoolRecord:
        if transaction.hash in self._transactions:
            raise ValueError(f"transaction '{transaction.hash}' already exists")

        record = MempoolRecord(
            transaction=transaction,
            status="pending",
            submittedAt=_local_now(),
        )
        self._transactions[transaction.hash] = record
        return record

    def getTransaction(self, txHash: str) -> Optional[MempoolRecord]:
        return self._transactions.get(txHash)

    def pendingTransactions(self) -> list[MempoolRecord]:
        return [
            record
            for record in self._transactions.values()
            if record.status == "pending"
        ]


def _local_now() -> str:
    return datetime.now().astimezone().isoformat()
