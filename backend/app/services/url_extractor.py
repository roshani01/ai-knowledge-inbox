import ipaddress
import socket
from typing import Optional, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import httpx
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.core.errors import SSRFSecurityError, UrlFetchError
from backend.app.core.logging import logger

DISALLOWED_HOSTS: Set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",
}


class ExtractedWebPage(BaseModel):
    title: str
    content: str
    url: str


def is_ip_allowed(ip_str: str) -> bool:
    """
    Validates whether an IP address is a safe public address.
    Rejects private, loopback, link-local, reserved, multicast, or cloud metadata ranges.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False

        # Explicit cloud metadata check
        if str(ip) == "169.254.169.254":
            return False

        return True
    except ValueError:
        return False


def validate_url_for_ssrf(url: str) -> None:
    """
    Enforces SSRF protection by verifying the URL scheme, hostname, and resolved IP addresses.
    Raises SSRFSecurityError if any check fails.
    """
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SSRFSecurityError(f"Malformed URL: {exc}")

    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFSecurityError(f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError("URL must contain a valid hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in DISALLOWED_HOSTS or hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        raise SSRFSecurityError(f"Requests to '{hostname}' are blocked for security.")

    # Check if the hostname is a direct IP address literal
    try:
        ip = ipaddress.ip_address(hostname)
        if not is_ip_allowed(str(ip)):
            raise SSRFSecurityError(f"Requests to restricted IP address '{hostname}' are blocked.")
        return
    except ValueError:
        # Hostname is a domain name, proceed to DNS resolution check
        pass

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    try:
        addr_infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        logger.warning("DNS resolution failed for %s: %s", hostname, e)
        raise UrlFetchError(f"Unable to resolve host '{hostname}'. Verify the domain name.")

    resolved_ips = {info[4][0] for info in addr_infos}
    for resolved_ip in resolved_ips:
        if not is_ip_allowed(resolved_ip):
            logger.warning("SSRF blocked: host %s resolved to restricted IP %s", hostname, resolved_ip)
            raise SSRFSecurityError(
                f"Host '{hostname}' resolved to a restricted IP address ({resolved_ip}). Access denied."
            )


def extract_readable_text(html_content: str, default_title: str) -> tuple[str, str]:
    """
    Parses HTML content using BeautifulSoup, removes noisy non-content elements,
    and returns a clean (title, readable_text) tuple.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        if h1 and h1.text:
            title = h1.text.strip()
    if not title:
        title = default_title

    # Remove non-text/irrelevant tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "iframe", "form"]):
        tag.decompose()

    # Extract readable text
    text = soup.get_text(separator="\n")
    # Clean up excessive blank lines and leading/trailing spaces
    lines = [line.strip() for line in text.splitlines()]
    clean_text = "\n".join(chunk for chunk in lines if chunk)

    return title, clean_text


async def fetch_and_extract_url(url: str) -> ExtractedWebPage:
    """
    Safely fetches a webpage with SSRF revalidation on redirects, size limits,
    content-type verification, and extracts human-readable text.
    """
    current_url = url
    max_redirects = 3
    redirect_count = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AI-Knowledge-Inbox/1.0",
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(
        timeout=settings.URL_REQUEST_TIMEOUT_SECONDS,
        follow_redirects=False,
    ) as client:
        while redirect_count <= max_redirects:
            validate_url_for_ssrf(current_url)

            try:
                response = await client.get(current_url, headers=headers)
            except httpx.TimeoutException:
                logger.warning("Timeout while fetching %s", current_url)
                raise UrlFetchError(f"Request timed out while connecting to {url}.")
            except httpx.RequestError as exc:
                logger.warning("HTTP request error fetching %s: %s", current_url, exc)
                raise UrlFetchError(f"Failed to fetch content from {url}: {exc}")

            # Handle redirects securely by revalidating target
            if response.is_redirect or response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    raise UrlFetchError(f"Server returned redirect status {response.status_code} without Location header.")
                next_url = urljoin(current_url, location)
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise UrlFetchError("Too many redirects encountered while fetching URL.")
                logger.info("Following safe redirect (%d/%d): %s -> %s", redirect_count, max_redirects, current_url, next_url)
                current_url = next_url
                continue

            if response.status_code >= 400:
                raise UrlFetchError(f"Webpage returned error status code: {response.status_code}")

            # Verify Content-Type
            content_type = response.headers.get("Content-Type", "").lower()
            if not any(t in content_type for t in ("text/html", "application/xhtml+xml", "text/plain")):
                raise UrlFetchError(
                    f"Unsupported content type '{content_type}'. Only HTML and plain text pages are supported."
                )

            # Check content length
            content_bytes = response.content
            if len(content_bytes) > settings.MAX_URL_RESPONSE_BYTES:
                raise UrlFetchError(
                    f"Page size ({len(content_bytes)} bytes) exceeds maximum limit of {settings.MAX_URL_RESPONSE_BYTES} bytes."
                )

            html_text = response.text
            parsed_url = urlparse(current_url)
            default_title = parsed_url.hostname or "Saved Web Page"

            title, cleaned_text = extract_readable_text(html_text, default_title)

            if not cleaned_text:
                raise UrlFetchError("The target webpage did not contain any readable text.")

            return ExtractedWebPage(
                title=title[:500],
                content=cleaned_text,
                url=current_url,
            )

    raise UrlFetchError("Failed to fetch webpage due to redirect limits.")
