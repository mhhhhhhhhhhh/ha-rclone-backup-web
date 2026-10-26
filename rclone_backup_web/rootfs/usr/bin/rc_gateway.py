#!/usr/bin/env python3
"""Loopback-only RC gateway. No raw input or backend errors are logged/returned."""
import http.client
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 5572
MAX_CONFIG_BODY = 2 * 1024 * 1024
HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade", "content-length", "host"}

MESSAGES = {
    "STATE_LOST": "Die Anmeldesitzung ist abgelaufen. Starte die iCloud-Anmeldung erneut.",
    "MFA_EMPTY": "Bitte gib einen MFA-Code ein.",
    "MFA_INVALID": "Der MFA-Code wurde nicht akzeptiert. Prüfe den Code oder starte die Anmeldung erneut.",
    "AUTH_FAILED": "Die Anmeldung wurde abgelehnt. Prüfe deine Zugangsdaten.",
    "UNKNOWN_STATE": "Der Anmeldeablauf konnte nicht fortgesetzt werden. Starte die Einrichtung erneut.",
    "PORT_BUSY": "address already in use",
    "REQUEST_FAILED": "Die rclone-Anfrage ist fehlgeschlagen. Es werden keine Eingabedaten angezeigt.",
}

def safe_error(raw, status=500):
    # Match categories only; NEVER interpolate any backend-supplied value.
    if isinstance(raw, dict):
        raw = raw.get("error", raw.get("Error", ""))
    text = raw.lower() if isinstance(raw, str) else ""
    if "session" in text and any(x in text for x in ("lost", "expired", "corrupt", "invalid")):
        code = "STATE_LOST"
    elif "unknown state" in text:
        code = "UNKNOWN_STATE"
    elif "blank" in text and "code" in text:
        code = "MFA_EMPTY"
    elif ("code" in text or "verification" in text) and any(x in text for x in ("invalid", "incorrect", "failed", "wrong", "not valid")):
        code = "MFA_INVALID"
    elif "address already in use" in text:
        code = "PORT_BUSY"
    elif any(x in text for x in ("invalid password", "incorrect password", "authentication failed", "invalid credentials")):
        code = "AUTH_FAILED"
    else:
        code = "REQUEST_FAILED"
    return {"error": MESSAGES[code], "code": code, "status": status}

class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def body_chunks(self):
        if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
            while True:
                line = self.rfile.readline(8192)
                size = int(line.split(b";", 1)[0].strip(), 16)
                if size == 0:
                    while self.rfile.readline(8192) not in (b"\r\n", b"\n", b""):
                        pass
                    break
                remaining = size
                while remaining:
                    part = self.rfile.read(min(65536, remaining))
                    if not part: raise ValueError("incomplete body")
                    remaining -= len(part)
                    yield part
                if self.rfile.read(2) != b"\r\n": raise ValueError("invalid chunk")
        else:
            remaining = int(self.headers.get("Content-Length", "0"))
            if remaining < 0: raise ValueError("invalid length")
            while remaining:
                part = self.rfile.read(min(65536, remaining))
                if not part: raise ValueError("incomplete body")
                remaining -= len(part)
                yield part

    def reply_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)
        self.close_connection = True

    def forward(self):
        conn = None
        try:
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
                self.reply_json(400, safe_error(None, 400)); return
            config_call = parsed.path.startswith("/config/")
            headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_HEADERS and k.lower() not in {"authorization", "origin"}}
            headers["Accept-Encoding"] = "identity"
            upstream_path = self.path
            if config_call and self.command in {"POST", "PUT", "PATCH"}:
                chunks=[]; total=0
                for chunk in self.body_chunks():
                    total+=len(chunk)
                    if total > MAX_CONFIG_BODY:
                        self.reply_json(413, safe_error(None, 413)); return
                    chunks.append(chunk)
                raw_body=b"".join(chunks)
                form = {k: values[-1] for k, values in parse_qs(parsed.query, keep_blank_values=True).items()}
                if raw_body:
                    content_type=self.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        extra=json.loads(raw_body)
                        if not isinstance(extra,dict): raise ValueError("invalid body")
                        form.update(extra)
                    elif "application/x-www-form-urlencoded" in content_type:
                        form.update({k:v[-1] for k,v in parse_qs(raw_body.decode(),keep_blank_values=True).items()})
                    else: raise ValueError("unsupported config body")
                for key in ("parameters", "opt"):
                    if isinstance(form.get(key),str): form[key]=json.loads(form[key])
                body=json.dumps(form).encode()
                upstream_path=parsed.path
                headers["Content-Type"]="application/json"
                headers["Content-Length"]=str(len(body))
            else:
                body=self.body_chunks()
                if self.headers.get("Content-Length") is not None:
                    headers["Content-Length"]=self.headers["Content-Length"]
                else:
                    headers["Transfer-Encoding"]="chunked"
            conn=http.client.HTTPConnection(UPSTREAM_HOST,UPSTREAM_PORT,timeout=180)
            conn.request(self.command,upstream_path,body=body,headers=headers,encode_chunked=True)
            response=conn.getresponse()
            if response.status >= 400:
                raw=response.read(1024*1024)
                try: payload=json.loads(raw)
                except (ValueError,UnicodeError): payload=None
                self.reply_json(response.status,safe_error(payload,response.status)); return
            if config_call and "json" in response.getheader("Content-Type", ""):
                raw=response.read(MAX_CONFIG_BODY+1)
                if len(raw)>MAX_CONFIG_BODY: raise ValueError("oversized configuration response")
                payload=json.loads(raw) if raw else {}
                if isinstance(payload,dict):
                    if payload.get("error"):
                        self.reply_json(500,safe_error(payload,500)); return
                    payload.pop("input",None)
                    if payload.get("Error"):
                        payload["Error"]=safe_error(payload["Error"])["error"]
                    option=payload.get("Option")
                    if isinstance(option,dict) and option.get("IsPassword"):
                        option["Default"]=""
                self.reply_json(response.status,payload); return
            self.send_response(response.status)
            for key,value in response.getheaders():
                if key.lower() not in HOP_HEADERS: self.send_header(key,value)
            length=response.getheader("Content-Length")
            if length is not None: self.send_header("Content-Length",length)
            self.send_header("Connection","close")
            self.end_headers()
            if self.command!="HEAD":
                while True:
                    chunk=response.read(65536)
                    if not chunk: break
                    self.wfile.write(chunk)
            self.close_connection=True
        except (BrokenPipeError,ConnectionResetError):
            self.close_connection=True
        except (ValueError,UnicodeError,OverflowError):
            self.reply_json(400,safe_error(None,400))
        except (OSError,http.client.HTTPException,socket.timeout):
            self.reply_json(502,safe_error(None,502))
        finally:
            if conn is not None: conn.close()

    do_GET=forward
    do_POST=forward
    do_PUT=forward
    do_PATCH=forward
    do_DELETE=forward
    do_HEAD=forward
    do_OPTIONS=forward

class QuietServer(ThreadingHTTPServer):
    daemon_threads=True
    def handle_error(self,*_):
        # Prevent traceback/request data from reaching logs.
        pass

if __name__=="__main__":
    QuietServer(("127.0.0.1",5573),Gateway).serve_forever()
