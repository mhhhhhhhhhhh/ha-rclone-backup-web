#!/usr/bin/env python3
"""Adapt upstream Rclone Web to the per-session Home Assistant ingress path.
Run inside the downloaded upstream source tree before npm run build.
Fail rather than silently produce an unpatched UI when upstream changes.
"""
from pathlib import Path
import re


def require_replace(path: str, pattern: str, replacement: str, minimum: int = 1) -> None:
    file = Path(path)
    source = file.read_text(encoding="utf-8")
    result, count = re.subn(pattern, lambda _: replacement, source)
    if count < minimum:
        raise SystemExit(f"Ingress patch no longer matches {path}: {pattern!r}")
    file.write_text(result, encoding="utf-8")
    print(f"Patched {path}: {count} match(es)")


def main() -> None:
    require_replace("src/router.tsx", r"\]\s*\)\s*;?\s*$",
                    "], { basename: window.__HA_INGRESS_PATH__ || '/' })\n")
    require_replace("src/lib/store.ts", r"name:\s*['\"]lite-auth-store['\"]",
                    "name: 'ha-rclone-web-auth'")
    require_replace("src/rclone/client.ts",
                    r"window\.location\.replace\(['\"]/login\?reason=auth['\"]\)",
                    "window.location.replace(`${window.__HA_INGRESS_PATH__}/login?reason=auth`)")
    require_replace("src/rclone/client.ts",
                    r"window\.location\.pathname === ['\"]/login['\"]",
                    "window.location.pathname === `${window.__HA_INGRESS_PATH__}/login`")
    # Keep uploads underneath /rc/ rather than escaping to the HA API root.
    require_replace("src/rclone/client.ts", r"const url = new URL\([^\n]*operations/uploadfile[^\n]*\)",
                    "const url = new URL(`${auth.url.replace(/\\/+$/, '')}/operations/uploadfile`)")
    # Upstream starts temporary HTTP servers for downloads. Proxy only loopback.
    require_replace("src/pages/RemotesDetails.tsx",
                    r"return `\$\{parsed\.protocol\}//\$\{parsed\.hostname\}:\$\{portMatch\[1\]\}`",
                    "return `${parsed.origin}${window.__HA_INGRESS_PATH__}/serve/${portMatch[1]}`")
    require_replace("src/pages/RemotesDetails.tsx", r"addr:\s*['\"]:0['\"]",
                    "addr: '127.0.0.1:0'")
    # Replace absolute public asset paths used by JSX src attributes.
    for file in Path("src").rglob("*.tsx"):
        source = file.read_text(encoding="utf-8")
        source = re.sub(r'''src=["'](/[^"']+\.(?:svg|png|ico|jpg|webp))["']''',
                        lambda m: "src={window.__HA_INGRESS_PATH__ + " + repr(m.group(1)) + "}", source)
        file.write_text(source, encoding="utf-8")
    Path("src/ha-ingress.d.ts").write_text(
        "interface Window { __HA_INGRESS_PATH__: string }\n", encoding="utf-8")
    index = Path("index.html")
    html = index.read_text(encoding="utf-8")
    # Relative public icon links; Vite handles the JS/CSS assets via --base ./.
    html = re.sub(r'''(["'])/([^"']+\.(?:svg|png|ico))\1''',
                  lambda m: m.group(1) + "./" + m.group(2) + m.group(1), html)
    bootstrap = Path("/patch/ingress-bootstrap.html").read_text(encoding="utf-8")
    if "<head>" not in html:
        raise SystemExit("Missing HTML head; ingress bootstrap was not injected.")
    html = html.replace("<head>", "<head>\n" + bootstrap, 1)
    index.write_text(html, encoding="utf-8")
    print("Ingress bootstrap and public asset paths patched.")


if __name__ == "__main__":
    main()
