"""Exercise navigation rendered by the patched OWHTTPD server."""

from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import pytest
import requests

pytestmark = pytest.mark.integration


class Navigation(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.base = None
        self.links = []
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base":
            self.base = attrs.get("href")
        elif tag == "a":
            self.current = [attrs.get("href", ""), ""]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


@pytest.mark.parametrize("path", ["/", "/bus.0", "/bus.0/", "/uncached/bus.0/"])
def test_nested_navigation(compose_project, path):
    response = requests.get("http://localhost:8099" + path, timeout=10)
    response.raise_for_status()
    nav = Navigation(response.text)
    assert nav.base is not None
    # Simulate the public URL: ingress strips this prefix before proxying.
    root = "https://ha.example/api/hassio_ingress/test-token/"
    base = urljoin(root + path.lstrip("/"), nav.base)
    assert base == root
    for href, label in nav.links:
        if urlsplit(href).scheme:
            continue
        resolved = urljoin(base, href)
        assert resolved.startswith(root)
        if label == "Bus listing" or label == "top":
            assert resolved == root
        elif label == "up":
            parent = path.rstrip("/").rpartition("/")[0] + "/"
            assert resolved == root + parent.lstrip("/")
        else:
            # Follow device/directory links to detect duplicated path segments.
            target = "http://localhost:8099/" + resolved[len(root):]
            requests.get(target, timeout=10).raise_for_status()
