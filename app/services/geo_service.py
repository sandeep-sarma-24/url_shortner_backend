import json
import logging
import time
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

PRIVATE_IP_PREFIXES = ("127.", "10.", "172.16.", "172.17.", "172.18.", "172.19.",
                       "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                       "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                       "172.30.", "172.31.", "192.168.", "0.", "::1", "fd", "fe80")

COUNTRY_NAMES: dict[str, str] = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AR": "Argentina",
    "AU": "Australia", "AT": "Austria", "BD": "Bangladesh", "BE": "Belgium",
    "BR": "Brazil", "CA": "Canada", "CL": "Chile", "CN": "China",
    "CO": "Colombia", "HR": "Croatia", "CZ": "Czechia", "DK": "Denmark",
    "EG": "Egypt", "FI": "Finland", "FR": "France", "DE": "Germany",
    "GR": "Greece", "HK": "Hong Kong", "HU": "Hungary", "IN": "India",
    "ID": "Indonesia", "IR": "Iran", "IQ": "Iraq", "IE": "Ireland",
    "IL": "Israel", "IT": "Italy", "JP": "Japan", "KE": "Kenya",
    "KR": "South Korea", "MY": "Malaysia", "MX": "Mexico", "NL": "Netherlands",
    "NZ": "New Zealand", "NG": "Nigeria", "NO": "Norway", "PK": "Pakistan",
    "PE": "Peru", "PH": "Philippines", "PL": "Poland", "PT": "Portugal",
    "RO": "Romania", "RU": "Russia", "SA": "Saudi Arabia", "SG": "Singapore",
    "ZA": "South Africa", "ES": "Spain", "SE": "Sweden", "CH": "Switzerland",
    "TW": "Taiwan", "TH": "Thailand", "TR": "Turkey", "UA": "Ukraine",
    "AE": "UAE", "GB": "United Kingdom", "US": "United States", "VN": "Vietnam",
}

_PUBLIC_IP_TTL_SECONDS = 60
_public_ip_cache: tuple[str, float] | None = None


def is_private_ip(ip: str) -> bool:
    if not ip:
        return True
    return any(ip.startswith(prefix) for prefix in PRIVATE_IP_PREFIXES)


def _fetch_current_public_ip() -> str | None:
    """Fetch the current outgoing public IP with a short-lived TTL cache.

    The cache expires after 60 seconds so VPN / network changes are picked
    up quickly without hammering external services on every request.
    """
    global _public_ip_cache
    if _public_ip_cache is not None:
        cached_ip, cached_at = _public_ip_cache
        if time.time() - cached_at < _PUBLIC_IP_TTL_SECONDS:
            return cached_ip

    for service_url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            req = Request(service_url, headers={"User-Agent": "shortr/1.0"})
            with urlopen(req, timeout=5) as resp:
                ip = resp.read().decode().strip()
                if ip and not is_private_ip(ip):
                    _public_ip_cache = (ip, time.time())
                    logger.info("Resolved outgoing public IP: %s", ip)
                    return ip
        except Exception as e:
            logger.debug("Failed to fetch public IP from %s: %s", service_url, e)
    return None


def get_client_ip(request) -> str | None:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return None


def _lookup_from_ipinfo(ip: str) -> dict | None:
    """Call ipinfo.io for a given IP and return parsed geo dict, or None on failure."""
    try:
        req = Request(
            f"https://ipinfo.io/{ip}/json",
            headers={"Accept": "application/json", "User-Agent": "shortr/1.0"},
        )
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if data.get("bogon"):
            logger.warning("ipinfo.io flagged %s as bogon", ip)
            return None

        lat, lon = None, None
        loc = data.get("loc")
        if loc and "," in loc:
            parts = loc.split(",")
            lat, lon = float(parts[0]), float(parts[1])

        cc = data.get("country", "")
        return {
            "country": COUNTRY_NAMES.get(cc, cc),
            "country_code": cc,
            "region": data.get("region"),
            "city": data.get("city"),
            "latitude": lat,
            "longitude": lon,
            "timezone": data.get("timezone"),
            "isp": data.get("org"),
        }
    except (URLError, ValueError, KeyError, IndexError) as e:
        logger.warning("Geolocation lookup failed for %s: %s", ip, e)
    except Exception as e:
        logger.warning("Geolocation lookup failed for %s: %s", ip, e)
    return None


def lookup_ip_location(ip: str) -> dict:
    """Resolve geo-location using ipinfo.io (free tier: 50k req/month).

    When the client IP is private (localhost / Docker gateway), fetches the
    current outgoing public IP on every call so VPN/network changes are
    reflected immediately.
    """
    default = {
        "country": None, "country_code": None, "region": None,
        "city": None, "latitude": None, "longitude": None,
        "timezone": None, "isp": None,
    }

    lookup_ip = ip
    if not ip or is_private_ip(ip):
        logger.info("Client IP %s is private, resolving current public IP", ip)
        lookup_ip = _fetch_current_public_ip()
        if not lookup_ip:
            logger.warning("Could not determine public IP, returning default geo")
            return default

    logger.info("Geo lookup for IP: %s (original client IP: %s)", lookup_ip, ip)
    result = _lookup_from_ipinfo(lookup_ip)
    return result if result else default
