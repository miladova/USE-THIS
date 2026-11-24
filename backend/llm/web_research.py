"""Normalize source citations returned by native provider web-search tools."""

from __future__ import annotations

from urllib.parse import urlsplit
from typing import Any

from backend.api.error_protocol import DomainApiError


def extract_verified_source_urls(report: str) -> list[str]:
    """Read only the server-rendered, numbered source appendix from a research report."""
    urls: list[str] = []
    for line in report.splitlines():
        if not line.startswith("[S") or "] " not in line or " — " not in line:
            continue
        url = line.rsplit(" — ", 1)[-1].strip()
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname and url not in urls:
            urls.append(url)
    return urls


def build_verified_source_appendix(sources: list[dict[str, Any]], *, minimum_sources: int = 3) -> str:
    """Create a dossier appendix only from URLs and claim links returned by web search.

    Args:
        sources: Provider-grounded source entries with ``url``, ``title`` and claim excerpts.
        minimum_sources: Minimum number of distinct cited source URLs required.
    Returns:
        Server-rendered bibliography and claim-to-source map.
    Raises:
        DomainApiError: Search did not yield enough valid HTTPS, claim-linked citations.
    """
    unique: dict[str, dict[str, Any]] = {}
    for source in sources:
        url = source.get("url") if isinstance(source, dict) else None
        title = source.get("title") if isinstance(source, dict) else None
        claims = source.get("claims", []) if isinstance(source, dict) else []
        if not isinstance(url, str) or not isinstance(title, str):
            continue
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or not title.strip():
            continue
        clean_claims = list(dict.fromkeys(
            claim.strip()[:500] for claim in claims
            if isinstance(claim, str) and len(claim.strip()) >= 20
        ))[:5]
        if clean_claims:
            unique.setdefault(url, {"url": url, "title": title.strip()[:300], "claims": clean_claims})
    if len(unique) < minimum_sources:
        raise DomainApiError(
            "HISTORICAL_RESEARCH_SOURCES_INSUFFICIENT",
            "联网历史研究未能返回至少三条可核验的 HTTPS 来源及其对应证据；为避免无来源写作，本章已停止生成",
            status_code=502,
        )
    lines = ["\n\n## Live-search verified citations and supporting passages"]
    for index, source in enumerate(unique.values(), 1):
        lines.append(f"[S{index}] {source['title']} — {source['url']}")
        for claim in source["claims"]:
            lines.append(f"  Search-grounded passage: {claim}")
    return "\n".join(lines)
