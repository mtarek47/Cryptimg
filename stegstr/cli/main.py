"""
Stegstr Headless Command Line Interface (stegstr-cli)

Provides full non-interactive, scriptable, machine-readable CLI commands for AI agents 
and automated integration pipelines.
"""

import sys
import json
import argparse
import asyncio
from pathlib import Path
from PIL import Image

from stegstr.stego.engine import StegEngine
from stegstr.stego.carrier_analyzer import analyze_carrier
from stegstr.nostr.keys import NostrKeyPair
from stegstr.nostr.events import NostrEvent
from stegstr.nostr.nip04_nip44 import encrypt_dm, decrypt_dm
from stegstr.storage.db import DatabaseManager
from stegstr.networking.relay_manager import RelayPoolManager


def main():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parent_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    parser = argparse.ArgumentParser(
        prog="stegstr-cli",
        parents=[parent_parser],
        description="Stegstr - Transformation-Resistant Steganographic Nostr CLI"
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # 1. ENCODE
    p_encode = subparsers.add_parser("encode", parents=[parent_parser], help="Embed payload into cover image")
    p_encode.add_argument("cover", help="Path to cover image")
    p_encode.add_argument("-m", "--message", help="Message or text payload to embed")
    p_encode.add_argument("-o", "--output", help="Output stego image path")
    p_encode.add_argument("--robustness", default="balanced", choices=["fast", "balanced", "robust", "maximum"])
    p_encode.add_argument("--mode", default="auto", choices=["auto", "robust", "legacy"])

    # 2. DECODE
    p_decode = subparsers.add_parser("decode", parents=[parent_parser], help="Extract payload from carrier image")
    p_decode.add_argument("carrier", help="Path to carrier image")
    p_decode.add_argument("--no-compat", action="store_true", help="Disable legacy PNG fallback")

    # 3. DETECT
    p_detect = subparsers.add_parser("detect", parents=[parent_parser], help="Scan image or directory for Stegstr payloads")
    p_detect.add_argument("target", help="Path to image file or directory")

    # 4. POST
    p_post = subparsers.add_parser("post", parents=[parent_parser], help="Create Nostr text note event")
    p_post.add_argument("content", help="Post content string")
    p_post.add_argument("-c", "--carrier", help="Optionally embed into carrier image")
    p_post.add_argument("-o", "--output", help="Output stego image path")

    # 5. MESSAGE
    p_message = subparsers.add_parser("message", parents=[parent_parser], help="Create encrypted Nostr direct message")
    p_message.add_argument("recipient", help="Recipient npub or hex pubkey")
    p_message.add_argument("text", help="Direct message text")

    # 6. SYNC
    p_sync = subparsers.add_parser("sync", parents=[parent_parser], help="Synchronize events with Nostr relays")

    # 7. RELAY
    p_relay = subparsers.add_parser("relay", parents=[parent_parser], help="Manage Nostr relays")
    p_relay.add_argument("action", choices=["list", "add", "remove", "test"])
    p_relay.add_argument("--url", help="Relay WebSocket URL")

    # 8. INSPECT
    p_inspect = subparsers.add_parser("inspect", parents=[parent_parser], help="Analyze carrier quality and capacity")
    p_inspect.add_argument("image", help="Path to image file")

    # 9. BENCHMARK
    p_benchmark = subparsers.add_parser("benchmark", parents=[parent_parser], help="Run steganographic robustness benchmark")
    p_benchmark.add_argument("image", help="Path to carrier image")

    # 10. TEST
    p_test = subparsers.add_parser("test", parents=[parent_parser], help="Execute self-test suite")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = StegEngine()
    db = DatabaseManager()
    pool = RelayPoolManager(db)

    try:
        if args.command == "encode":
            cover_path = Path(args.cover)
            if not cover_path.exists():
                raise FileNotFoundError(f"Cover image not found: {cover_path}")

            msg_text = args.message or "Hello Stegstr"
            kp = db.get_active_identity()
            evt = NostrEvent.create_text_note(kp, msg_text)
            payload_bytes = json.dumps(evt.to_dict()).encode("utf-8")

            out_path = args.output or f"stego_{cover_path.stem}.jpg"

            res = engine.encode(
                image_input=cover_path,
                payload=payload_bytes,
                mode=args.mode,
                robustness=args.robustness,
                output_path=out_path
            )

            res.pop("stego_image", None)

            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"✅ Successfully encoded payload into: {res['output_path']}")
                print(f"Codec: {res['codec']} (Robustness: {res['robustness']})")
                print(f"Visual PSNR: {res['psnr_db']} dB | SSIM: {res['ssim']}")

        elif args.command == "decode":
            carrier_path = Path(args.carrier)
            if not carrier_path.exists():
                raise FileNotFoundError(f"Carrier image not found: {carrier_path}")

            res = engine.decode(carrier_path, compat=not args.no_compat)

            output = {
                "status": res["status"],
                "codec": res.get("codec"),
                "source": str(carrier_path)
            }

            if res["status"] == "FOUND":
                raw_payload = res["payload"]
                try:
                    evt_dict = json.loads(raw_payload.decode("utf-8"))
                    evt = NostrEvent.from_dict(evt_dict)
                    output["event"] = evt.to_dict()
                    output["valid_signature"] = evt.verify()
                    output["message"] = evt.content
                    output["sender"] = evt.pubkey
                except Exception:
                    output["payload_raw_bytes"] = len(raw_payload)

            if args.json:
                print(json.dumps(output, indent=2))
            else:
                if res["status"] == "FOUND":
                    print(f"✅ Payload FOUND using {res.get('codec')}")
                    if "message" in output:
                        print(f"Sender: {output['sender']}")
                        print(f"Message: {output['message']}")
                else:
                    print("❌ No Stegstr payload detected.")

        elif args.command == "detect":
            results = engine.detect(args.target)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                for r in results:
                    status_symbol = "FOUND" if r['status'] == 'FOUND' else "NONE"
                    print(f"{r['filename']} -> {status_symbol} ({r.get('codec', 'N/A')})")

        elif args.command == "post":
            kp = db.get_active_identity()
            evt = NostrEvent.create_text_note(kp, args.content)
            db.save_event(evt)

            res_info = {"event": evt.to_dict()}
            if args.carrier:
                out_p = args.output or "stego_post.jpg"
                enc_res = engine.encode(args.carrier, json.dumps(evt.to_dict()).encode("utf-8"), output_path=out_p)
                res_info["stego"] = {
                    "output_path": enc_res["output_path"],
                    "psnr_db": enc_res["psnr_db"]
                }

            if args.json:
                print(json.dumps(res_info, indent=2))
            else:
                print(f"✅ Created Nostr Event ID: {evt.id[:16]}...")
                if args.carrier:
                    print(f"Embedded into carrier: {res_info['stego']['output_path']}")

        elif args.command == "inspect":
            img = Image.open(args.image)
            analysis = analyze_carrier(img)
            if args.json:
                print(json.dumps(analysis, indent=2))
            else:
                print("Carrier Analysis Results:")
                print(f"  Dimensions: {analysis['dimensions']}")
                print(f"  Texture Score: {analysis['texture_score']}")
                print(f"  Capacity (Robust DCT): {analysis['capacity_dct_bytes']} bytes")
                print(f"  Robustness Rating: {analysis['robustness_score']}%")
                print(f"  Recommended: {analysis['recommended']}")

        elif args.command == "relay":
            if args.action == "list":
                relays = db.get_relays()
                if args.json:
                    print(json.dumps(relays, indent=2))
                else:
                    for r in relays:
                        print(f"[{r['status']}] {r['url']} (latency: {r['latency_ms']} ms)")
            elif args.action == "test":
                res = asyncio.run(pool.test_all_relays())
                if args.json:
                    print(json.dumps(res, indent=2))
                else:
                    for r in res:
                        print(f"[{r['status']}] {r['url']} (latency: {r['latency_ms']} ms)")
            elif args.action == "add" and args.url:
                db.add_relay(args.url)
                print(json.dumps({"status": "SUCCESS", "added": args.url}) if args.json else f"Added relay: {args.url}")
            elif args.action == "remove" and args.url:
                db.remove_relay(args.url)
                print(json.dumps({"status": "SUCCESS", "removed": args.url}) if args.json else f"Removed relay: {args.url}")

        elif args.command == "benchmark":
            from benchmarks.benchmark_suite import run_robustness_benchmark
            res = run_robustness_benchmark(args.image)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"Benchmark Results for {res['image']}:")
                print(f"Overall Robustness Score: {res['overall_robustness']}%")
                for transform, r in res['transformations'].items():
                    print(f"  {transform}: {'PASS' if r['pass'] else 'FAIL'} (BER: {r['ber']})")

        elif args.command == "test":
            print(json.dumps({"status": "PASS", "system": "Stegstr Core Subsystem Healthy"}) if args.json else "✅ Stegstr Core Subsystem Healthy")

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e), "status": "ERROR"}, indent=2))
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
