"""URL normalisation and domain validation for Peacock Crawler."""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


_DEFAULT_PORTS = {"http": 80, "https": 443}
_HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


class UrlValidationError(ValueError):
    """Raised when a seed URL / domain is not crawlable."""


@dataclass(slots=True, frozen=True)
class NormalisedUrl:
    original: str
    normalised: str
    scheme: str
    hostname: str
    port: int | None
    path: str
    is_ip_host: bool


def validate_domain(hostname: str) -> str:
    host = (hostname or "").strip().lower().rstrip(".")
    if not host:
        raise UrlValidationError("Hostname is empty")
    if host == "localhost":
        return host
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    if not _HOST_RE.match(host):
        raise UrlValidationError(f"Invalid hostname: {hostname}")
    if "." not in host and host != "localhost":
        raise UrlValidationError(f"Hostname missing public suffix: {hostname}")
    return host


def resolve_dns(hostname: str) -> list[str]:
    infos = socket.getaddrinfo(hostname, None)
    return sorted({item[4][0] for item in infos})


def normalise_url(url: str, *, base: str | None = None) -> NormalisedUrl:
    raw = (url or "").strip()
    if not raw:
        raise UrlValidationError("URL is empty")
    if base:
        raw = urljoin(base, raw)

    parts = urlsplit(raw)
    scheme = (parts.scheme or "https").lower()
    if scheme not in {"http", "https"}:
        raise UrlValidationError(f"Unsupported scheme: {scheme}")

    hostname = parts.hostname
    if not hostname:
        raise UrlValidationError(f"URL missing hostname: {url}")
    host = validate_domain(hostname)

    port = parts.port
    default_port = _DEFAULT_PORTS[scheme]
    netloc = host
    if port and port != default_port:
        netloc = f"{host}:{port}"

    path = parts.path or "/"
    # Collapse duplicate slashes in path (not query)
    while "//" in path:
        path = path.replace("//", "/")
    # Strip trailing slash except for site root
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    # Stable query ordering; drop empty fragments
    query_items = parse_qsl(parts.query, keep_blank_values=True)
    query = urlencode(sorted(query_items))

    normalised = urlunsplit((scheme, netloc, path, query, ""))
    is_ip = False
    try:
        ipaddress.ip_address(host)
        is_ip = True
    except ValueError:
        is_ip = host == "localhost"

    return NormalisedUrl(
        original=url,
        normalised=normalised,
        scheme=scheme,
        hostname=host,
        port=port,
        path=path,
        is_ip_host=is_ip,
    )


def is_same_host(a: str, b: str) -> bool:
    try:
        return normalise_url(a).hostname == normalise_url(b).hostname
    except UrlValidationError:
        return False


def absolutise(link: str, base_url: str) -> str | None:
    try:
        return normalise_url(link, base=base_url).normalised
    except UrlValidationError:
        return None
