"""3.1.0 · Opening a web link from an answer or the 「网页」 panel in the user's own browser.

The page never navigates: it asks for ``open_link`` with the address it shows. Leo checks the
address itself, asks in a native Windows dialog (a page script cannot click it), and only then
hands it to the system browser. Anything that is not a plain public http(s) address is refused:
other schemes (``file:``, ``ms-*:``, ``javascript:``), user names in the address (the classic
``good.example@evil.example`` disguise), and this computer or its private network, where Leo's
own services live.
"""
from __future__ import annotations

import ipaddress
import re
import socket
import threading
import unicodedata
import webbrowser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

LINK_INVALID = "WORKBENCH_LINK_INVALID"
MAX_URL_LENGTH = 2048
_LOCAL_SUFFIXES = (".localhost", ".localdomain", ".local", ".internal", ".lan", ".home.arpa")
# Names that answer as 127.0.0.1 for whatever the visitor asked. The literal is a public-looking
# hostname, so the syntactic checks below do not see a local address.
_LOOPBACK_ALIASES = ("localtest.me", "lvh.me", "vcap.me", "nip.io", "sslip.io", "xip.io", "traefik.me")
# Browsers read numeric shorthands such as 127.1, 0x7f.0.0.1 or 2130706433 as IPv4 addresses.
_NUMERIC_HOST = re.compile(r"(?:0x[0-9a-f]*|[0-9]+)(?:\.(?:0x[0-9a-f]*|[0-9]+)){0,3}")
_LOOKUP_SECONDS = 2.0


def _is_global(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    mapped = getattr(address, "ipv4_mapped", None)
    if mapped is not None:
        address = mapped
    return bool(address.is_global)


def _lookup(host: str):
    """Addresses for *host*.

    ``None`` means the name does not resolve. ``"timeout"`` means the lookup did not
    finish, or the name could not be encoded: either one can still be this machine,
    so callers treat it as local. A finished negative answer is not itself local.
    """
    found: dict = {}

    def resolve() -> None:
        try:
            found["infos"] = socket.getaddrinfo(host, None)
        except socket.gaierror:
            found["error"] = True
        except Exception:
            found["invalid"] = True

    worker = threading.Thread(target=resolve, name="leo-link-lookup", daemon=True)
    worker.start()
    worker.join(_LOOKUP_SECONDS)
    if worker.is_alive() or found.get("invalid"):
        return "timeout"
    if found.get("error") or "infos" not in found:
        return None
    return found["infos"]


def _is_machine_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Loopback, link-local or a private LAN. Benchmark ranges are not included.

    Some local resolvers answer every public name from 198.18.0.0/15. Treating
    that range as this machine would refuse every ordinary website.
    """
    mapped = getattr(address, "ipv4_mapped", None)
    if mapped is not None:
        address = mapped
    if address.is_loopback or address.is_link_local or address.is_unspecified or address.is_multicast:
        return True
    if isinstance(address, ipaddress.IPv4Address):
        return any(address in ipaddress.ip_network(cidr) for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
    return address in ipaddress.ip_network("fc00::/7")


def _resolves_locally(host: str) -> bool:
    """True when any answer is this machine or its LAN, or the lookup did not finish.

    A name that does not resolve is not itself local: ordinary sites are opened even
    when this computer cannot resolve them. A lookup that is still running after the
    deadline is local, because it can answer with a private address a moment later.
    """
    infos = _lookup(host)
    if infos == "timeout":
        return True
    if not infos:
        return False
    try:
        addresses = [ipaddress.ip_address(info[4][0].split("%", 1)[0]) for info in infos]
    except (ValueError, TypeError, IndexError):
        return True
    return any(_is_machine_address(address) for address in addresses)


def browser_host(host: str) -> str:
    """The host as a browser reads it: one percent-decode, then a trailing dot removed.

    ``127.0.0.1%2e`` is not an address to ``ipaddress``, and it is ``127.0.0.1`` in
    Chromium. A null byte or a broken escape is refused rather than left to the browser.
    """
    if "%" not in host:
        return host.lower().rstrip(".")
    raw = bytearray()
    index = 0
    while index < len(host):
        if host[index] != "%":
            raw.extend(host[index].encode("utf-8"))
            index += 1
            continue
        digits = host[index + 1:index + 3]
        if len(digits) != 2 or any(character not in "0123456789abcdefABCDEF" for character in digits):
            raise ValueError(LINK_INVALID)
        byte = int(digits, 16)
        if byte == 0:
            raise ValueError(LINK_INVALID)
        raw.append(byte)
        index += 3
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(LINK_INVALID) from None
    return decoded.lower().rstrip(".")


def endpoint_host_forbidden(host: str) -> bool:
    """True when a model base URL is not a public name and not this machine's loopback.

    Loopback stays allowed: a local OpenAI-compatible server is a supported endpoint.
    Private, link-local and obfuscated numeric hosts are not. A percent-encoded host
    is refused so the saved address is the address the person typed. Saving a profile
    does not resolve DNS.
    """
    if "%" in host or any(unicodedata.category(character) == "Cf" for character in host):
        return True
    name = browser_host(host)
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        # 2130706433 and 0x7f.0.0.1 are not Python addresses; a browser may still
        # read them as one. A dotted name is resolved later, by the provider.
        return bool(_NUMERIC_HOST.fullmatch(name))
    mapped = getattr(address, "ipv4_mapped", None)
    if mapped is not None:
        address = mapped
    if address.is_loopback or address.is_global:
        return False
    return True


def _alias_for_local(name: str) -> bool:
    return any(name == alias or name.endswith("." + alias) for alias in _LOOPBACK_ALIASES)


def _refused_address(host: str) -> bool:
    """True for this machine, private networks and any address a browser might read as one."""
    name = browser_host(host)
    try:
        return not _is_global(ipaddress.ip_address(name))
    except ValueError:
        pass
    # A public site always has a dot; a bare name (localhost, router, nas) is on this network.
    if "." not in name or name.endswith(_LOCAL_SUFFIXES) or bool(_NUMERIC_HOST.fullmatch(name)):
        return True
    # localtest.me and 127.0.0.1.nip.io are ordinary names that resolve to this machine.
    if _alias_for_local(name) or _resolves_locally(name):
        return True
    return False


def validate_url(value: object) -> str:
    """Return the address to open, or raise ``ValueError(LINK_INVALID)``."""
    if not isinstance(value, str) or not value or len(value) > MAX_URL_LENGTH:
        raise ValueError(LINK_INVALID)
    if any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F or unicodedata.category(ch) == "Cf" for ch in value):
        raise ValueError(LINK_INVALID)
    try:
        parts = urlsplit(value)
        host = parts.hostname or ""
        parts.port  # noqa: B018 -- reading it raises for a malformed port
    except ValueError:
        raise ValueError(LINK_INVALID) from None
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        raise ValueError(LINK_INVALID)
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        raise ValueError(LINK_INVALID)
    if _refused_address(host):
        raise ValueError(LINK_INVALID)
    return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path, parts.query, parts.fragment))


def describe_host(url: str) -> str:
    """The site as the dialog shows it; an internationalised name also shows its ASCII form."""
    host = urlsplit(url).hostname or ""
    if any(unicodedata.category(ch) == "Cf" for ch in host):
        return "（主机名含不可见字符）"
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return host.encode("ascii", "backslashreplace").decode("ascii")
    return host if ascii_host == host else f"{host}（{ascii_host}）"


class _RedirectSeen(Exception):
    def __init__(self, status: int, location: str):
        self.status = status
        self.location = location


class _StopRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise _RedirectSeen(code, newurl)


def _probe_redirect(url: str):
    """``(status, location)`` for one request. HEAD first; GET when HEAD is refused.

    The body is not read. A redirect is reported instead of followed.
    """
    opener = build_opener(ProxyHandler({}), _StopRedirect())

    def once(method):
        request = Request(url, method=method, headers={"User-Agent": "LeoAI-link-check"})
        try:
            with opener.open(request, timeout=5) as response:
                return response.status, response.headers.get("Location")
        except _RedirectSeen as seen:
            return seen.status, seen.location
        except HTTPError as error:
            location = error.headers.get("Location") if error.headers else None
            return error.code, location

    status, location = once("HEAD")
    if status in (405, 501):
        return once("GET")
    return status, location


def resolve_redirects(url: str, *, probe=None, hops: int = 4) -> str:
    """The public address a browser would land on, or ``LINK_INVALID``.

    Each HTTP redirect is checked with the same rules as the original address.
    When the site cannot be contacted there is no redirect to reject, so the
    already-validated address is returned. A page script can still navigate
    after the browser has loaded it; the confirmation says so.
    """
    current = url
    fetch = probe or _probe_redirect
    for _ in range(hops):
        try:
            status, location = fetch(current)
        except (URLError, TimeoutError, OSError):
            return current
        if not isinstance(status, int) or not 300 <= status < 400:
            return current
        if not isinstance(location, str) or not location:
            raise ValueError(LINK_INVALID)
        current = validate_url(urljoin(current, location))
    raise ValueError(LINK_INVALID)


def confirm_native(window, title: str, text: str) -> bool:
    """OK/Cancel box owned by the Leo window. Unlike the close guard, any failure means no."""
    try:
        import ctypes
        user32 = ctypes.WinDLL("user32")
    except Exception:
        return False
    owner = 0
    try:
        owner = window.native.Handle.ToInt64() if window is not None else 0
    except Exception:
        owner = 0
    try:
        # MB_OKCANCEL | MB_ICONQUESTION | MB_DEFBUTTON2 | MB_SETFOREGROUND: cancelling is the default.
        return user32.MessageBoxW(owner, text, title, 0x1 | 0x20 | 0x100 | 0x10000) == 1
    except Exception:
        return False


class LinkOpener:
    """The ``open_link`` operation. ``confirm`` and ``launch`` are replaceable for tests."""

    def __init__(self, window_getter, *, confirm=confirm_native, launch=webbrowser.open_new_tab,
                 resolve=None):
        self._window_getter = window_getter
        self._confirm = confirm
        self._launch = launch
        self._resolve = resolve or resolve_redirects

    def open(self, payload) -> dict:
        url = validate_url(payload.get("url") if isinstance(payload, dict) else None)
        destination = self._resolve(url)
        text = ("即将用系统浏览器打开这个网页：\n\n" + destination + "\n\n网站：" + describe_host(destination))
        if destination != url:
            text += "\n\n原链接会跳转到这个地址，打开的是跳转之后的网址：\n" + url
        text += "\n\n这个链接来自回答或 AI 读过的网页。页面打开之后，它自己的脚本仍可能再跳转。只在你信任它时打开。"
        try:
            window = self._window_getter()
        except Exception:
            window = None
        if not self._confirm(window, "打开网页链接", text):
            return {"opened": False}
        return {"opened": bool(self._launch(destination))}
