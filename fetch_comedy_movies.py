"""Fetch comedy movies from TMDB and write titles to comedy_movies.txt.

TMDB comedy genre id = 35. Discover is paginated (20 movies per page; API max 500 pages).

Examples:
  python fetch_comedy_movies.py                  # first 25 pages (~500 titles), quick
  python fetch_comedy_movies.py --pages 5        # first 5 pages
  python fetch_comedy_movies.py --all            # all pages (slow)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
COMEDY_GENRE_ID = 35
BASE = "https://api.themoviedb.org/3/discover/movie"
OUT_FILE = "comedy_movies.txt"
TMDB_MAX_PAGES = 500


def fetch_page(page: int) -> dict:
    params = {
        "with_genres": str(COMEDY_GENRE_ID),
        "include_adult": "false",
        "include_video": "false",
        "language": "en-US",
        "sort_by": "popularity.desc",
        "page": str(page),
    }
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def main() -> None:
    if not API_KEY:
        print("Set TMDB_API_KEY in .env", file=sys.stderr)
        sys.exit(1)

    p = argparse.ArgumentParser(description="Write comedy movie titles from TMDB to a txt file.")
    p.add_argument(
        "--all",
        action="store_true",
        help=f"Fetch every page (up to {TMDB_MAX_PAGES}; can take several minutes).",
    )
    p.add_argument(
        "--pages",
        type=int,
        default=25,
        metavar="N",
        help="Max pages to fetch (ignored if --all). Default: 25",
    )
    p.add_argument("-o", "--output", default=OUT_FILE, help=f"Output file (default: {OUT_FILE})")
    args = p.parse_args()
    out_path = args.output

    titles: list[str] = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        data = fetch_page(page)
        total_pages = min(int(data.get("total_pages") or 0), TMDB_MAX_PAGES)
        if args.all:
            last_page = total_pages
        else:
            last_page = min(total_pages, max(1, args.pages))

        for m in data.get("results") or []:
            t = (m.get("title") or "").strip()
            if t:
                titles.append(t)

        print(f"Page {page}/{last_page} - {len(titles)} titles", flush=True)
        page += 1
        if page > last_page:
            break

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(titles))

    print(f"Wrote {len(titles)} titles to {out_path}")


if __name__ == "__main__":
    main()
