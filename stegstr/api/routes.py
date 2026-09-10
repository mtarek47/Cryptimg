"""
Stegstr REST API Routes & OpenAPI Endpoints
"""

import io
import json
import base64
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from pydantic import BaseModel
from PIL import Image

from stegstr.stego.engine import StegEngine
from stegstr.stego.carrier_analyzer import analyze_carrier
from stegstr.storage.db import DatabaseManager
from stegstr.nostr.keys import NostrKeyPair
from stegstr.nostr.events import NostrEvent
from stegstr.nostr.nip04_nip44 import encrypt_dm, decrypt_dm
from stegstr.networking.relay_manager import RelayPoolManager
from benchmarks.benchmark_suite import run_robustness_benchmark

router = APIRouter(prefix="/api/v1")
engine = StegEngine()
db = DatabaseManager()
pool = RelayPoolManager(db)


def resolve_keypair(key_str: Optional[str] = None) -> NostrKeyPair:
    if key_str:
        clean = key_str.strip()
        try:
            if clean.startswith("nsec"):
                return NostrKeyPair.from_nsec(clean)
            return NostrKeyPair(clean)
        except Exception:
            pass
    return db.get_active_identity()


@router.post("/identity/new")
def api_generate_identity() -> Dict[str, Any]:
    kp = NostrKeyPair()
    return {
        "pubkey": kp.public_key_hex,
        "privkey": kp.private_key_hex,
        "npub": kp.npub,
        "nsec": kp.nsec
    }


class PostNoteRequest(BaseModel):
    text: str


class PostMessageRequest(BaseModel):
    recipient: str
    text: str


class EncodeRequest(BaseModel):
    message: str
    robustness: Optional[str] = "balanced"
    mode: Optional[str] = "auto"


@router.get("/status")
def get_status(x_nostr_privkey: Optional[str] = Header(None)) -> Dict[str, Any]:
    active_kp = resolve_keypair(x_nostr_privkey)
    return {
        "status": "ONLINE",
        "system": "Crypt Engine V2",
        "identity": {
            "npub": active_kp.npub,
            "pubkey": active_kp.public_key_hex
        },
        "version": "1.0.0"
    }


@router.get("/relays")
def get_relays() -> List[Dict[str, Any]]:
    return db.get_relays()


@router.post("/relays/test")
def api_test_relays() -> List[Dict[str, Any]]:
    try:
        relays = db.get_relays()
        results = [pool.test_relay_sync(r["url"]) for r in relays]
        return results
    except Exception as e:
        return [{"status": "ERROR", "error": str(e)}]


@router.post("/posts")
def api_post_note(req: PostNoteRequest, x_nostr_privkey: Optional[str] = Header(None)) -> Dict[str, Any]:
    try:
        kp = resolve_keypair(x_nostr_privkey)
        evt = NostrEvent.create_text_note(kp, req.text)
        db.save_event(evt)
        return {
            "status": "CREATED",
            "event_id": evt.id
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


@router.post("/posts/{event_id}/unsend")
def api_unsend_note(event_id: str, x_nostr_privkey: Optional[str] = Header(None)) -> Dict[str, Any]:
    try:
        evt = db.get_event_by_id(event_id)
        if not evt:
            raise HTTPException(status_code=404, detail="Message not found")
        
        kp = resolve_keypair(x_nostr_privkey)
        if evt["pubkey"] != kp.public_key_hex:
            raise HTTPException(status_code=403, detail="Permission denied: You can only unsend your own messages")
        
        # Check 2-minute (120-second) window
        import time
        now = int(time.time())
        if now - evt["created_at"] > 120:
            raise HTTPException(status_code=400, detail="Unsend window expired: Messages can only be un-sent within 2 minutes")
        
        deleted = db.delete_event(event_id)
        return {
            "status": "SUCCESS",
            "message": "Message un-sent successfully",
            "event_id": event_id
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


@router.post("/encode")
async def api_encode(
    file: UploadFile = File(...),
    message: str = Form(...),
    robustness: str = Form("balanced"),
    mode: str = Form("auto"),
    sender_privkey: Optional[str] = Form(None),
    x_nostr_privkey: Optional[str] = Header(None)
) -> Dict[str, Any]:
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        kp = resolve_keypair(sender_privkey or x_nostr_privkey)
        evt = NostrEvent.create_text_note(kp, message)
        payload_bytes = json.dumps(evt.to_dict()).encode("utf-8")

        res = engine.encode(img, payload_bytes, mode=mode, robustness=robustness)
        
        stego_img = res.pop("stego_image", None)
        if stego_img:
            buf = io.BytesIO()
            if mode == "legacy" or mode == "png":
                stego_img.save(buf, format="PNG")
                mime = "image/png"
            else:
                stego_img.save(buf, format="JPEG", quality=95, subsampling=0)
                mime = "image/jpeg"
            b64_out = base64.b64encode(buf.getvalue()).decode('utf-8')
            res["stego_image_base64"] = f"data:{mime};base64,{b64_out}"

        return res
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


@router.post("/decode")
async def api_decode(
    file: UploadFile = File(...),
    x_nostr_privkey: Optional[str] = Header(None)
) -> Dict[str, Any]:
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        res = engine.decode(img)
        
        pkt = res.get("packet")
        if pkt and hasattr(pkt, "to_dict"):
            res["packet"] = pkt.to_dict()
        else:
            res["packet"] = None

        if res["status"] == "FOUND" and res.get("payload"):
            raw_payload = res["payload"]
            if isinstance(raw_payload, bytes):
                try:
                    evt_dict = json.loads(raw_payload.decode("utf-8"))
                    evt = NostrEvent.from_dict(evt_dict)
                    res["event"] = evt.to_dict()
                    res["valid_signature"] = evt.verify()
                    
                    if evt.kind == 4:
                        kp = resolve_keypair(x_nostr_privkey)
                        try:
                            res["message"] = decrypt_dm(kp, evt)
                        except Exception:
                            res["message"] = evt.content
                    else:
                        res["message"] = evt.content

                    res["sender"] = evt.pubkey
                    res["payload"] = res["message"]
                except Exception:
                    res["payload"] = raw_payload.decode("utf-8", errors="ignore")
        else:
            res["payload"] = None

        return res
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


@router.post("/detect")
async def api_detect(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        res = engine.decode(img)
        return {
            "filename": file.filename,
            "status": res["status"],
            "codec": res.get("codec")
        }
    except Exception as e:
        return {
            "filename": file.filename,
            "status": "ERROR",
            "error": str(e)
        }


@router.post("/benchmark")
async def api_benchmark(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        res = run_robustness_benchmark(img, robustness="robust")
        res["image"] = file.filename
        return res
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


@router.post("/messages")
def api_post_message(req: PostMessageRequest, x_nostr_privkey: Optional[str] = Header(None)) -> Dict[str, Any]:
    try:
        kp = resolve_keypair(x_nostr_privkey)
        evt = encrypt_dm(kp, req.recipient, req.text)
        db.save_event(evt)
        return {
            "status": "CREATED",
            "event_id": evt.id,
            "recipient": req.recipient
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


@router.get("/messages")
def api_get_messages(x_nostr_privkey: Optional[str] = Header(None)) -> List[Dict[str, Any]]:
    kp = resolve_keypair(x_nostr_privkey)
    raw_events = db.get_events(kind=4, limit=100) or []
    messages = []
    for item in raw_events:
        item_copy = dict(item)
        evt = NostrEvent.from_dict(item_copy)
        try:
            item_copy["decrypted_text"] = decrypt_dm(kp, evt)
            item_copy["decrypted_success"] = True
        except Exception:
            item_copy["decrypted_text"] = item_copy.get("content")
            item_copy["decrypted_success"] = False
        messages.append(item_copy)
    return messages


@router.get("/feed")
def api_get_feed(limit: int = 50, x_nostr_privkey: Optional[str] = Header(None)) -> List[Dict[str, Any]]:
    kp = resolve_keypair(x_nostr_privkey)
    raw_events = db.get_events(limit=limit) or []
    processed = []

    for item in raw_events:
        item_copy = dict(item)
        if item_copy.get("kind") == 4:
            evt = NostrEvent.from_dict(item_copy)
            try:
                item_copy["decrypted_content"] = decrypt_dm(kp, evt)
                item_copy["is_dm"] = True
            except Exception:
                item_copy["decrypted_content"] = item_copy.get("content")
                item_copy["is_dm"] = True
        else:
            item_copy["is_dm"] = False
        processed.append(item_copy)

    return processed
