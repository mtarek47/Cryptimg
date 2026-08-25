"""
Standard Library Pure Python WebSocket Client

Implements RFC 6455 WebSocket client using Python built-in socket and ssl modules.
Requires zero external pip dependencies.
"""

import socket
import ssl
import os
import struct
import base64
import urllib.parse
from typing import Optional, Tuple


class WebSocketClient:
    def __init__(self, url: str, timeout: float = 5.0):
        self.url = url
        self.timeout = timeout
        self.parsed = urllib.parse.urlparse(url)
        self.scheme = self.parsed.scheme
        self.host = self.parsed.hostname
        self.port = self.parsed.port or (443 if self.scheme in ("wss", "https") else 80)
        self.path = self.parsed.path or "/"
        if self.parsed.query:
            self.path += "?" + self.parsed.query

        self.sock: Optional[socket.socket] = None

    def connect(self):
        raw_sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        if self.scheme in ("wss", "https"):
            context = ssl.create_default_context()
            self.sock = context.wrap_socket(raw_sock, server_hostname=self.host)
        else:
            self.sock = raw_sock

        sec_key = base64.b64encode(os.urandom(16)).decode('utf-8')
        handshake = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {sec_key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode('utf-8'))

        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            response += chunk

        if b"101 Switching Protocols" not in response:
            raise ConnectionError(f"WebSocket handshake failed: {response[:100]!r}")

    def send_text(self, text: str):
        payload = text.encode('utf-8')
        length = len(payload)
        mask = os.urandom(4)

        header = bytearray()
        header.append(0x81)  # Text frame

        if length <= 125:
            header.append(0x80 | length)
        elif length <= 65535:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))

        header.extend(mask)

        masked_payload = bytearray(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + bytes(masked_payload))

    def recv_text(self) -> str:
        header = self._recv_exact(2)
        b1, b2 = header[0], header[1]
        
        length = b2 & 0x7F
        if length == 126:
            length_bytes = self._recv_exact(2)
            length = struct.unpack("!H", length_bytes)[0]
        elif length == 127:
            length_bytes = self._recv_exact(8)
            length = struct.unpack("!Q", length_bytes)[0]

        has_mask = bool(b2 & 0x80)
        mask = self._recv_exact(4) if has_mask else None

        data = self._recv_exact(length)
        if has_mask:
            data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))

        return data.decode('utf-8', errors='ignore')

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Socket closed prematurely")
            buf.extend(chunk)
        return bytes(buf)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
