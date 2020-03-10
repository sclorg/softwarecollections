"""HTTP Forwarded Header middleware tests"""

import functools
import socket
from ipaddress import ip_address
from itertools import accumulate
from types import MappingProxyType
from typing import Any
from typing import Callable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple

import pytest
from django.core.exceptions import MiddlewareNotUsed
from django.http.request import HttpRequest
from django.test import RequestFactory
from softwarecollections.middleware import forwarded

IPAddress = forwarded.IPAddress
Middleware = forwarded.HttpForwardedMiddleware
MiddlewareFactory = Callable[..., Middleware]

TESTING_DOMAIN: str = "testing-cluster.local"
TRUSTED_FQDN: str = "trusted-proxy." + TESTING_DOMAIN
DISTRUSTED_FQDN: str = "distrusted." + TESTING_DOMAIN

PROXIED_DOMAIN: str = "webapp.exposed"
INTERNAL_DOMAIN: str = "webapp.internal"
CLIENT_ADDR: IPAddress = ip_address("2001:db8::1")


class NetworkModel:
    """Simple network model for monkey-patching socket primitives."""

    def __init__(
        self,
        host_map: Mapping[IPAddress, Optional[str]],
        search_path: Optional[Sequence[str]] = None,
    ):
        """Initialize network.

        Arguments:
            host_map: Mapping from IP address to FQDN.
                Used by ``gethostbyaddr`` and ``gethostbyname``.
            search_path: DNS search path. Used by ``getfqdn``.
        """

        self.by_addr = MappingProxyType(host_map)
        self.by_host = MappingProxyType({host: ip for ip, host in host_map.items()})
        self.search_path = search_path

    def getfqdn(
        self, name: Optional[str] = None, *, default: str = "testing.machine"
    ) -> str:
        """Simulate socket.getfqdn."""

        if not name:
            return default

        if "." in name:
            return name

        for suffix in self.search_path:
            candidate = ".".join([name, suffix])
            if candidate in self.by_host:
                return candidate
        else:
            return name

    def gethostbyaddr(self, addr: str) -> Tuple[str, List[str], List[str]]:
        """Simulate socket.gethostbyaddr"""

        try:
            hostname = self.by_addr[ip_address(addr)]
        except KeyError:
            raise socket.herror(1, "Unknown host")

        # The FQDN might not be the primary host name
        # Return short host name as the primary, with other variants as aliases
        alias_iter = accumulate(hostname.split("."), lambda *sides: ".".join(sides))

        return next(alias_iter), list(alias_iter), [addr]


def format_forwarded(
    by: Optional[IPAddress] = None,
    client: IPAddress = CLIENT_ADDR,
    host: str = PROXIED_DOMAIN,
    proto: str = "http",
):
    """Properly format HTTP Forwarded header."""

    def format_ip(addr: IPAddress) -> str:
        return str(addr) if addr.version == 4 else '"[{!s}]"'.format(addr)

    field_map = {
        "by": format_ip(by) if by is not None else None,
        "for": format_ip(client),
        "host": host,
        "proto": proto,
    }

    return ";".join(
        "{0}={1}".format(key, value) for key, value in field_map.items() if value
    )


@pytest.fixture(autouse=True)
def mock_network(monkeypatch: "pytest.monkeypatch.MonkeyPatch") -> NetworkModel:
    """Mock network calls in middleware."""

    network = NetworkModel(
        host_map={
            ip_address("192.0.2.42"): TRUSTED_FQDN,
            ip_address("198.51.100.42"): None,
            ip_address("203.0.113.42"): DISTRUSTED_FQDN,
        },
        search_path=["testing-cluster.local"],
    )

    monkeypatch.setattr(forwarded, "getfqdn", network.getfqdn)
    monkeypatch.setattr(forwarded, "gethostbyaddr", network.gethostbyaddr)

    return network


@pytest.fixture(scope="session")
def middleware_factory() -> MiddlewareFactory:
    """Middleware factory with defaults that prevents side effects."""

    return functools.partial(
        Middleware,
        lambda request: request,
        enabled=True,
        trusted_proxy_set=frozenset(),
    )


@pytest.fixture
def middleware(
    middleware_factory: MiddlewareFactory, mock_network: NetworkModel,
) -> Middleware:
    """Prepared middleware instance that trusts some proxies on the mocked network."""

    trusted = {
        mock_network.by_host[None],
        mock_network.by_host[TRUSTED_FQDN],
    }

    return middleware_factory(trusted_proxy_set=trusted)


@pytest.fixture
def http_request(rf: RequestFactory) -> HttpRequest:
    """Testing HTTP Request object."""

    instance = rf.get("/")
    instance.META["HTTP_HOST"] = INTERNAL_DOMAIN
    instance.META["REMOTE_ADDR"] = ip_address("::")  # unspecified address
    return instance


@pytest.fixture
def request_from_trusted(
    mock_network: NetworkModel, http_request: HttpRequest
) -> HttpRequest:
    """Request from implicitly trusted proxy."""

    http_request.META["HTTP_FORWARDED"] = format_forwarded(
        by=mock_network.by_host[TRUSTED_FQDN]
    )
    return http_request


@pytest.fixture
def request_from_distrusted(
    mock_network: NetworkModel, http_request: HttpRequest
) -> HttpRequest:
    """Request from implicitly distrusted proxy."""

    http_request.META["HTTP_FORWARDED"] = format_forwarded(
        by=mock_network.by_host[DISTRUSTED_FQDN]
    )
    return http_request


@pytest.fixture
def secure_request(
    mock_network: NetworkModel, http_request: HttpRequest
) -> HttpRequest:
    """Request originally made with HTTPS"""

    http_request.META["HTTP_FORWARDED"] = format_forwarded(
        by=mock_network.by_host[TRUSTED_FQDN], proto="https",
    )
    return http_request


@pytest.fixture
def request_from_proxy_chain(
    mock_network: NetworkModel, http_request: HttpRequest
) -> HttpRequest:
    """Request that was passed by multiple (possibly distrusted) proxies."""

    TRUSTED_IP = mock_network.by_host[TRUSTED_FQDN]
    DISTRUSTED_IP = mock_network.by_host[DISTRUSTED_FQDN]

    chain = [
        format_forwarded(by=TRUSTED_IP),
        format_forwarded(by=DISTRUSTED_IP, client=TRUSTED_IP),
        format_forwarded(by=TRUSTED_IP, client=DISTRUSTED_IP),
    ]

    http_request.META["HTTP_FORWARDED"] = ", ".join(chain)
    return http_request


def test_middleware_is_not_used_without_being_explicitly_enabled(
    settings: Any, middleware_factory: MiddlewareFactory,
):
    """Middleware is not used without being explicitly enabled in settings."""

    del settings.USE_HTTP_FORWARDED

    with pytest.raises(MiddlewareNotUsed):
        middleware_factory(enabled=None)


def test_middleware_is_used_when_explicitly_enabled(
    settings: Any, middleware_factory: MiddlewareFactory,
):
    """Middleware can be used when explicitly enabled."""

    settings.USE_HTTP_FORWARDED = True
    middleware_factory(enabled=None)


def test_middleware_loads_trusted_proxy_from_settings(
    settings: Any, middleware_factory: MiddlewareFactory, mock_network: NetworkModel,
):
    """List of trusted proxies is loaded from setting."""

    TRUSTED_HOST = "trusted-proxy"
    TRUSTED_ADDR = "198.51.100.42"

    settings.HTTP_FORWARDED_TRUSTED_PROXY_SET = [TRUSTED_HOST, TRUSTED_ADDR]
    middleware = middleware_factory(trusted_proxy_set=None)

    assert middleware._trusted_addr_set == {ip_address(TRUSTED_ADDR)}
    assert middleware._trusted_fqdn_set == {mock_network.getfqdn(TRUSTED_HOST)}


def test_trust_proxy_by_ip(
    middleware_factory: MiddlewareFactory, mock_network: NetworkModel
):
    """Trusted proxy can be specified by IP address."""

    TRUSTED = mock_network.by_host[TRUSTED_FQDN]

    middleware = middleware_factory(trusted_proxy_set={str(TRUSTED)})

    assert middleware.trusts(TRUSTED)


def test_trust_proxy_by_fqdn(
    middleware_factory: MiddlewareFactory, mock_network: NetworkModel
):
    """Trusted proxy can be specified by FQDN."""

    middleware = middleware_factory(trusted_proxy_set={TRUSTED_FQDN})

    assert middleware.trusts(mock_network.by_host[TRUSTED_FQDN])


def test_unknown_proxy_can_be_trusted(middleware_factory: MiddlewareFactory):
    """Middleware can trust unknown proxy."""

    middleware = middleware_factory(trusted_proxy_set={forwarded.UNKNOWN_ID})

    assert middleware.trusts(forwarded.UNKNOWN_ID)


def test_trust_proxy_by_partial_hostname(
    middleware_factory: MiddlewareFactory, mock_network: NetworkModel
):
    """Trusted proxy can be specified as partial (existing) host."""

    PARTIAL, __ = TRUSTED_FQDN.split(".", maxsplit=1)

    middleware = middleware_factory(trusted_proxy_set={PARTIAL})

    assert middleware.trusts(mock_network.by_host[TRUSTED_FQDN])


def test_trusted_proxy_sets_metadata(
    middleware: Middleware, request_from_trusted: HttpRequest
):
    """Middleware respects redirect by trusted proxy."""

    metadata = middleware(request_from_trusted).META

    assert metadata["HTTP_HOST"] == PROXIED_DOMAIN
    assert metadata["REMOTE_ADDR"] == CLIENT_ADDR


def test_distrusted_proxy_does_not_modify_metadata(
    middleware: Middleware, request_from_distrusted: HttpRequest
):
    """Middleware ignores redirects by distrusted proxy."""

    original = request_from_distrusted.META.copy()
    modified = middleware(request_from_distrusted).META

    assert modified == original


def test_furthest_trusted_proxy_from_chain_is_used(
    mock_network: NetworkModel,
    middleware: Middleware,
    request_from_proxy_chain: HttpRequest,
):
    """In proxy chain, the info from furthest connected trusted proxy is used."""

    metadata = middleware(request_from_proxy_chain).META

    assert metadata["HTTP_HOST"] == PROXIED_DOMAIN
    assert metadata["REMOTE_ADDR"] == mock_network.by_host[DISTRUSTED_FQDN]


def test_unsecure_request_stays_unsecure(
    middleware: Middleware, request_from_trusted: HttpRequest
):
    """Request originally made via HTTP stays unsecure."""

    request = middleware(request_from_trusted)

    assert not request.is_secure()


def test_secure_request_is_marked_as_secure(
    middleware: Middleware, secure_request: HttpRequest
):
    """Request originally made on via HTTPS is marked as secure."""

    request = middleware(secure_request)

    assert request.is_secure()
    assert request.build_absolute_uri("/").startswith("https://")
