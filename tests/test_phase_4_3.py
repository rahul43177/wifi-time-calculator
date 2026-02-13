"""
Tests for Phase 4.3: CSS Styling.

Covers:
- Static CSS file is served via /static/style.css
- Dashboard HTML links to external stylesheet (no inline styles)
- CSS contains required design tokens and class definitions
- Color coding classes exist: green (connected/completed), yellow (warning), red (disconnected)
- Responsive media query present
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_static_css_is_served() -> None:
    """GET /static/style.css should return 200 with CSS content-type."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "text/css" in content_type


@pytest.mark.asyncio
async def test_dashboard_links_external_stylesheet() -> None:
    """Dashboard HTML should reference /static/style.css via <link>."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert '<link rel="stylesheet" href="/static/style.css">' in response.text


@pytest.mark.asyncio
async def test_dashboard_has_no_inline_style_block() -> None:
    """Dashboard HTML should not contain an inline <style> block."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "<style>" not in response.text


@pytest.mark.asyncio
async def test_css_contains_color_tokens() -> None:
    """CSS should define green, yellow, and red color tokens."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert "--green:" in css
    assert "--yellow:" in css
    assert "--red:" in css
    assert "--progress-warning:" in css
    assert "--progress-complete:" in css


@pytest.mark.asyncio
async def test_css_contains_status_classes() -> None:
    """CSS should define .connected, .disconnected, and .warning classes."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert ".connected" in css
    assert ".disconnected" in css
    assert ".timer.warning" in css
    assert ".timer.completed" in css
    assert ".progress-fill.warning" in css
    assert ".progress-fill.complete" in css


@pytest.mark.asyncio
async def test_css_uses_monospace_timer_font() -> None:
    """Timer display should use a monospace font family for stable digit width."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert "monospace" in css


@pytest.mark.asyncio
async def test_css_has_responsive_media_query() -> None:
    """CSS should contain a responsive media query for small screens."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert "@media" in css
    assert "max-width" in css


@pytest.mark.asyncio
async def test_css_progress_bar_has_transition() -> None:
    """Progress bar fill should have a smooth transition."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert "transition" in css


@pytest.mark.asyncio
async def test_css_contains_hidden_utility_class() -> None:
    """CSS should define a .hidden utility class used by the completion banner."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert ".hidden" in css


@pytest.mark.asyncio
async def test_static_nonexistent_file_returns_404() -> None:
    """Requesting a non-existent static file should return 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/nonexistent.css")

    assert response.status_code == 404
