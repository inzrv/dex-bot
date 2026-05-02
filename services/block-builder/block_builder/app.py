from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from .mempool import Mempool
from .transaction import Transaction
from .ws import PendingTransactionBroadcaster


def create_app() -> FastAPI:
    app = FastAPI(title="DEX Local Block Builder")
    mempool = Mempool()
    pendingBroadcaster = PendingTransactionBroadcaster()

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/ping")
    async def ping() -> dict:
        return {"message": "pong"}

    @app.post("/public/tx")
    async def submit_public_tx(payload: dict) -> dict:
        try:
            transaction = Transaction.fromJson(payload)
            record = mempool.addTransaction(transaction)
            await pendingBroadcaster.broadcast(
                {
                    "type": "pending_transaction",
                    "record": record.toJson(),
                }
            )
            return record.toJson()
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/public/tx/{tx_hash}")
    async def get_public_tx(tx_hash: str) -> dict:
        record = mempool.getTransaction(tx_hash)
        if record is None:
            raise HTTPException(status_code=404, detail="transaction not found")
        return record.toJson()

    @app.get("/public/pending")
    async def get_pending_transactions() -> dict:
        return {
            "transactions": [
                record.toJson()
                for record in mempool.pendingTransactions()
            ]
        }

    @app.websocket("/ws/pending")
    async def pending_stream(websocket: WebSocket) -> None:
        await pendingBroadcaster.connect(websocket)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pendingBroadcaster.disconnect(websocket)

    return app
