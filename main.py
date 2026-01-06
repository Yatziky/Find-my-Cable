from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

DB_PATH = "data.db"

def get_db():
    return sqlite3.connect(DB_PATH)

# Data model for PUT requests
class DeviceUpdate(BaseModel):
    model: str
    owner: str
    status: str
    notes: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/device/{sn}")
async def get_device(sn: str):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM devices WHERE serial_number = ?", (sn,))
    row = cur.fetchone()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "serial_number": row[0],
        "model": row[1],
        "owner": row[2],
        "status": row[3],
        "notes": row[4]
    }

@app.put("/device/{sn}")
async def update_device(sn: str, data: DeviceUpdate):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM devices WHERE serial_number = ?", (sn,))
    if not cur.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Device not found")

    cur.execute("""
        UPDATE devices
        SET model=?, owner=?, status=?, notes=?
        WHERE serial_number=?
    """, (data.model, data.owner, data.status, data.notes, sn))
    db.commit()
    db.close()

    return {"success": True}
