#!/usr/bin/env python3
"""Codex Web Harvester

This script crawls a website starting from a root URL, extracts posts published
within a specified date range, and outputs the results as JSON.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional, Sequence, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0 (compatible; CodexWebHarvester/1.0; +https://openai.com)"
MAX_PAGES = 150
REQUEST_TIMEOUT = 15


@dataclass
class Post:
    title: str
    url: str
    published_at: datetime
    author: str
    text_excerpt: str
    media: List[str]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "author": self.author,
            "text_excerpt": self.text_excerpt,
            "media": self.media,
        }


try:
    from dateutil import parser as date_parser  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    date_parser = None


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl a website for posts within a date range.")
    parser.add_argument("url", help="Root URL to start crawling from.")
    parser.add_argument("start_date", help="Inclusive start date (ISO 8601 format recommended).")
    parser.add_argument("end_date", help="Inclusive end date (ISO 8601 format recommended).")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=MAX_PAGES,
        help=f"Maximum number of pages to crawl (default {MAX_PAGES}).",
    )
    return parser.parse_args(argv)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")
    if parsed.scheme not in {"http", "https"}:
        return ""
    normalized = parsed._replace(fragment="")
    return normalized.geturl()


def is_same_domain(url: str, root_netloc: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == root_netloc or parsed.netloc.endswith("." + root_netloc)


def fetch(session: requests.Session, url: str) -> Optional[requests.Response]:
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        if "text/html" not in response.headers.get("Content-Type", ""):
            return None
        return response
    except requests.RequestException:
        return None


META_DATE_ATTRIBUTES = [
    ("meta", {"property": "article:published_time"}),
    ("meta", {"property": "article:modified_time"}),
    ("meta", {"name": "pubdate"}),
    ("meta", {"name": "publish-date"}),
    ("meta", {"name": "PublishDate"}),
    ("meta", {"name": "date"}),
    ("meta", {"name": "dc.date"}),
    ("meta", {"itemprop": "datePublished"}),
    ("meta", {"itemprop": "dateModified"}),
]


def parse_date(value: str) -> Optional[datetime]:
    value = value.strip()
    if not value:
        return None
    try:
        # Try ISO format first
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    if date_parser:
        try:
            dt = date_parser.parse(value)
            if dt and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, OverflowError):
            pass
    try:
        dt = parsedate_to_datetime(value)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def extract_candidate_dates(soup: BeautifulSoup) -> List[datetime]:
    dates: List[datetime] = []
    for tag, attrs in META_DATE_ATTRIBUTES:
        element = soup.find(tag, attrs=attrs)
        if element and element.has_attr("content"):
            dt = parse_date(str(element["content"]))
            if dt:
                dates.append(dt)
    # Look for <time> elements
    for time_el in soup.find_all("time"):
        for attribute in ("datetime", "content"):
            if time_el.has_attr(attribute):
                dt = parse_date(str(time_el[attribute]))
                if dt:
                    dates.append(dt)
                    break
        else:
            dt = parse_date(time_el.get_text(strip=True))
            if dt:
                dates.append(dt)
    return dates


TITLE_SELECTORS = [
    ("meta", {"property": "og:title"}),
    ("meta", {"name": "twitter:title"}),
    ("meta", {"name": "title"}),
]


def extract_title(soup: BeautifulSoup) -> str:
    for tag, attrs in TITLE_SELECTORS:
        el = soup.find(tag, attrs=attrs)
        if el and el.has_attr("content"):
            content = str(el["content"]).strip()
            if content:
                return content
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.find(["h1", "h2"])
    if heading:
        return heading.get_text(strip=True)
    return ""


AUTHOR_META = [
    ("meta", {"name": "author"}),
    ("meta", {"property": "article:author"}),
    ("meta", {"name": "byl"}),
]


def extract_author(soup: BeautifulSoup) -> str:
    for tag, attrs in AUTHOR_META:
        el = soup.find(tag, attrs=attrs)
        if el and el.has_attr("content"):
            content = str(el["content"]).strip()
            if content:
                return content
    author_elements = soup.select('[rel="author"], .author, .byline, [itemprop="author"]')
    for el in author_elements:
        text = el.get_text(" ", strip=True)
        if text:
            return text
    return ""


MEDIA_TAGS = {
    "img": "src",
    "video": "src",
    "audio": "src",
    "source": "src",
}


def extract_media_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    urls: List[str] = []
    for tag, attr in MEDIA_TAGS.items():
        for element in soup.find_all(tag):
            src = element.get(attr)
            if not src:
                continue
            full = urljoin(base_url, src)
            if full not in urls:
                urls.append(full)
    return urls


EXCERPT_MAX_LENGTH = 320


def extract_text_excerpt(soup: BeautifulSoup) -> str:
    article = soup.find("article")
    text_source = article if article else soup.body
    if not text_source:
        return ""
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in text_source.find_all("p")
        if len(p.get_text(strip=True)) >= 20
    ]
    if not paragraphs:
        text = text_source.get_text(" ", strip=True)
    else:
        text = " ".join(paragraphs)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > EXCERPT_MAX_LENGTH:
        text = text[: EXCERPT_MAX_LENGTH - 3].rstrip() + "..."
    return text


def extract_post_from_page(url: str, soup: BeautifulSoup) -> Optional[Post]:
    title = extract_title(soup)
    dates = extract_candidate_dates(soup)
    if not dates:
        return None
    published_at = min(dates)
    author = extract_author(soup)
    text_excerpt = extract_text_excerpt(soup)
    media = extract_media_urls(soup, url)
    return Post(
        title=title,
        url=url,
        published_at=published_at,
        author=author,
        text_excerpt=text_excerpt,
        media=media,
    )


def crawl(root_url: str, start: datetime, end: datetime, max_pages: int = MAX_PAGES) -> List[Post]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    normalized_root = normalize_url(root_url)
    if not normalized_root:
        raise ValueError(f"Unsupported URL: {root_url}")

    root_netloc = urlparse(normalized_root).netloc
    queue: deque[str] = deque([normalized_root])
    visited: Set[str] = set()
    posts: List[Post] = []

    while queue and len(visited) < max_pages:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        response = fetch(session, current)
        if not response:
            continue

        page_url = response.url
        soup = BeautifulSoup(response.text, "html.parser")

        post = extract_post_from_page(page_url, soup)
        if post and start <= post.published_at <= end:
            posts.append(post)

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            if not href or href.startswith("mailto:") or href.startswith("javascript:"):
                continue
            absolute = normalize_url(urljoin(page_url, href))
            if not absolute:
                continue
            if absolute in visited:
                continue
            if not is_same_domain(absolute, root_netloc):
                continue
            queue.append(absolute)
    return posts


def ensure_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_interval(start_str: str, end_str: str) -> tuple[datetime, datetime]:
    start = parse_date(start_str)
    end = parse_date(end_str)
    if not start or not end:
        raise ValueError("Start and end dates must be parseable datetime strings.")
    start = ensure_timezone(start)
    end = ensure_timezone(end)
    if start > end:
        raise ValueError("Start date must be earlier than or equal to end date.")
    return start, end


def serialize_results(root_url: str, start: datetime, end: datetime, posts: Sequence[Post]) -> dict:
    return {
        "root_url": root_url,
        "interval": {
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "count": len(posts),
        "items": [post.to_dict() for post in posts],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        start, end = parse_interval(args.start_date, args.end_date)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        posts = crawl(args.url, start, end, max_pages=args.max_pages)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    results = serialize_results(args.url, start, end, posts)

    with open("results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
