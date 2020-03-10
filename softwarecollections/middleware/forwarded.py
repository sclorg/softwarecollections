"""Parse HTTP Forwarded header and overwrites relevant metadata.

See IETF RFC 7239 and/or
https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Forwarded
for details on this header.
"""

import logging
import re
from ipaddress import IPv4Address
from ipaddress import IPv6Address
from ipaddress import ip_address
from socket import getfqdn
from socket import gethostbyaddr
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Tuple
from typing import Union

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpRequest
from django.http import HttpResponse

IPAddress = Union[IPv4Address, IPv6Address]

UNKNOWN_ID: str = "unknown"

# Host identifier can optionally contain port number
_PORT_PATTERN = re.compile(r":(?P<number>\d+)$")

_log = logging.getLogger(__name__)
_log_msg_will_modify = "Will modify request: {details}"
_log_msg_wont_modify = "Won't modify request: {details}"


def _is_ip_address(instance: Any) -> bool:
    """Determine if instance is an IP address object."""

    return isinstance(instance, (IPv4Address, IPv6Address))


def _parse_ip_address(candidate: str) -> IPAddress:
    """Attempt to parse candidate as IP address.

    Arguments:
        candidate: IP address string, with optional port.
            The port is discarded if present.
            The candidate can contain quotes around the whole address.
            In case of IPv6, address brackets are also supported.

    Returns:
        Parsed IP address.

    Raises:
        ValueError: The candidate is not an IP address.
    """

    # Strip quotes, if any
    candidate = candidate.strip("\"'")
    # Discard port, if any
    address = _PORT_PATTERN.sub("", candidate)
    # Discard IPv6 brackets, if present
    address = address.strip("[]")

    return ip_address(address)


def _parse_header(payload: str) -> Iterator[Dict[str, Any]]:
    """Parse HTTP Forwarded header payload.

    Arguments:
        payload: The body of the HTTP header.

    Yields:
        Dictionary with processes payload data.

    Raises:
        ValueError: Malformed header.
    """

    def make_pair(item: str) -> Tuple[str, Union[str, IPAddress]]:
        """Transform item string into tuple."""

        key, value = (part.strip() for part in item.split("=", maxsplit=1))

        if key in {"for", "by"}:
            try:
                value = _parse_ip_address(value)
            except ValueError:
                pass  # Obfuscated or unknown identifiers are strings

        return key, value

    # Multiple redirects are separated by ','
    # Items are separated by ';'
    for redirect in payload.split(","):
        yield dict(make_pair(item) for item in redirect.split(";"))


class HttpForwardedMiddleware:
    """Parse HTTP Forwarded header and overwrites relevant request metadata.

    The current version of this middleware does not support
    obfuscated (i.e. ``_secret``) or ``unknown`` host identifiers.
    Any proxy that identifies itself by them will be distrusted,
    and any client that provides them will not modify ``REMOTE_ADDR`` metadata.

    Respected settings
    ==================

    USE_HTTP_FORWARDED
        Enable this middleware. This is a potentially insecure operation
        – see the core Django setting ``USE_X_FORWARDED_HOST`` for details;
        the same consideration should apply here.

    HTTP_FORWARDED_TRUSTED_PROXY_SET
        Iterable of trusted proxies,
        specified by either IP address(es) or host names.
        Defaults to an empty set.

        All values should be strings;
        any non-valid IP address is considered to be a host name.
    """

    def __init__(
        self,
        get_response: Callable,
        *,
        enabled: Optional[bool] = None,
        trusted_proxy_set: Optional[Iterable[str]] = None,
    ):
        """

        Keyword arguments:
            enabled: Whether this middleware should be enabled.
                If None, respects the ``USE_HTTP_FORWARDED`` Django setting.

            trusted_proxy_set: Base set of trusted proxies.
                If None, the value is taken
                from the ``HTTP_FORWARDED_TRUSTED_PROXY_SET`` Django setting.
        """

        log = logging.LoggerAdapter(_log, {"forwarded": None})

        if enabled is None:
            enabled = getattr(settings, "USE_HTTP_FORWARDED", False)
        if trusted_proxy_set is None:
            trusted_proxy_set = getattr(
                settings, "HTTP_FORWARDED_TRUSTED_PROXY_SET", frozenset()
            )

        if not enabled:
            raise MiddlewareNotUsed()

        # Split trusted proxies on IP adddresses and host names
        trusted_addr = set()
        trusted_fqdn = set()

        for host in trusted_proxy_set:
            try:
                trusted_addr.add(ip_address(host))
            except ValueError:
                trusted_fqdn.add(getfqdn(host))

        self._get_response = get_response
        log.debug("Trusting by address: %s", trusted_addr)
        self._trusted_addr_set = frozenset(trusted_addr)
        log.debug("Trusting by name: %s", trusted_fqdn)
        self._trusted_fqdn_set = frozenset(trusted_fqdn)

    def trusts(self, addr: Union[str, IPAddress]) -> bool:
        """Query if this middleware trusts proxy with given IP address.

        This accepts any host identifier from the Forwarded header,
        which includes obfuscated identifiers (i.e ``_hidden``, ``_secret``)
        and ``unknown`` identifier.
        However, any obfuscated or unknown host is always distrusted.
        """

        if not _is_ip_address(addr):  # unknown or obfuscated
            return False

        if addr in self._trusted_addr_set:
            return True

        primary, alias_seq, _addr_seq = gethostbyaddr(str(addr))

        return primary in self._trusted_fqdn_set or any(
            alias in self._trusted_fqdn_set for alias in alias_seq
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Modify request metadata according to the redirect information."""

        forward_info = {"forwarded": request.META.get("HTTP_FORWARDED")}
        log = logging.LoggerAdapter(_log, forward_info)

        if "HTTP_FORWARDED" not in request.META:
            log.debug(_log_msg_wont_modify.format(details="No Forwarded header"))
            return self._get_response(request)

        redirect_chain = list(_parse_header(request.META["HTTP_FORWARDED"]))
        if not redirect_chain:
            log.debug(_log_msg_wont_modify.format(details="Forwarded header is empty"))

        for redirect in reversed(redirect_chain):
            # Bail out on first distrusted proxy
            proxy = redirect.get("by", UNKNOWN_ID)
            if not self.trusts(proxy):
                log.debug("Ending request modification: [%s] is distrusted", proxy)
                break

            host = redirect.get("host", request.META["HTTP_HOST"])
            client = redirect.get("for", UNKNOWN_ID)
            if not _is_ip_address(client):
                client = request.META["REMOTE_ADDR"]

            log.debug(
                _log_msg_will_modify.format(details="Host: %s; Remote: %s"),
                host,
                client,
            )
            request.META["HTTP_HOST"] = host
            request.META["REMOTE_ADDR"] = client

        return self._get_response(request)
