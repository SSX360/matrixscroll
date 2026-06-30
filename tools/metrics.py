#!/usr/bin/env python3
"""Instrumentation tool to query and report Matrix Scroll adoption metrics across PyPI, GitHub, GitHub Actions, and Glama."""

import os
import sys
import json
import urllib.request
import urllib.error
import re

def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    # Add User-Agent to avoid blocking
    req.add_header("User-Agent", "MatrixScroll-Metrics/1.0")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_html(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"error: {e}"

def get_pypi_stats():
    res = fetch_json("https://pypistats.org/api/packages/matrixscroll/recent")
    if "error" in res:
        return None
    return res.get("data")

def get_github_stats(token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
        
    repo_data = fetch_json("https://api.github.com/repos/SSX360/matrixscroll", headers)
    action_data = fetch_json("https://api.github.com/repos/SSX360/matrixscroll-verify-action", headers)
    
    stats = {
        "repo_stars": repo_data.get("stargazers_count", 0) if "error" not in repo_data else "Error",
        "repo_forks": repo_data.get("forks_count", 0) if "error" not in repo_data else "Error",
        "action_stars": action_data.get("stargazers_count", 0) if "error" not in action_data else "Error",
        "action_forks": action_data.get("forks_count", 0) if "error" not in action_data else "Error",
    }
    
    if token:
        clones = fetch_json("https://api.github.com/repos/SSX360/matrixscroll/traffic/clones", headers)
        views = fetch_json("https://api.github.com/repos/SSX360/matrixscroll/traffic/views", headers)
        stats["clones_14d"] = clones.get("count", 0) if "error" not in clones else "Auth/Rate limit error"
        stats["views_14d"] = views.get("count", 0) if "error" not in views else "Auth/Rate limit error"
    else:
        stats["clones_14d"] = "Requires GITHUB_TOKEN"
        stats["views_14d"] = "Requires GITHUB_TOKEN"
        
    return stats

_GLAMA_BADGE = re.compile(
    r">([A-F])</div><span>([^<]+)</span>",
    re.IGNORECASE,
)


def _parse_glama_badges(html):
    """Extract license, quality, and maintenance letter grades from Glama SSR HTML."""
    quality = license_grade = maintenance = None
    for grade, label in _GLAMA_BADGE.findall(html):
        label_lower = label.strip().lower()
        if label_lower.startswith("license"):
            license_grade = grade.upper()
        elif label_lower == "quality":
            quality = grade.upper()
        elif label_lower == "maintenance":
            maintenance = grade.upper()
    return quality, license_grade, maintenance


def get_glama_registry_status():
    """Return Glama listing status for matrixscroll and digital-rain."""
    matrixscroll = fetch_json("https://glama.ai/api/mcp/v1/servers/SSX360/matrixscroll")
    digital_rain = fetch_json("https://glama.ai/api/mcp/v1/servers/SSX360/digital-rain")
    listing_html = fetch_html("https://glama.ai/mcp/servers/SSX360/matrixscroll")

    quality = license_grade = maintenance = None
    if isinstance(listing_html, str) and not listing_html.startswith("error:"):
        quality, license_grade, maintenance = _parse_glama_badges(listing_html)

    return {
        "matrixscroll_listed": isinstance(matrixscroll, dict) and "error" not in matrixscroll,
        "matrixscroll_id": matrixscroll.get("id") if isinstance(matrixscroll, dict) else None,
        "matrixscroll_quality": quality,
        "matrixscroll_license": license_grade,
        "matrixscroll_maintenance": maintenance,
        "digital_rain_listed": isinstance(digital_rain, dict) and "error" not in digital_rain,
        "digital_rain_id": digital_rain.get("id") if isinstance(digital_rain, dict) else None,
    }


def get_glama_favorites():
    html = fetch_html("https://glama.ai/mcp/servers/SSX360/matrixscroll")
    if not isinstance(html, str) or html.startswith("error:"):
        return "N/A"
    # Basic scraping for favorites count
    match = re.search(r'(\d+)\s+favorites', html, re.IGNORECASE)
    if match:
        return match.group(1)
    # Try another pattern
    match = re.search(r'icon-favorite.*?>\s*(\d+)', html, re.IGNORECASE)
    if match:
        return match.group(1)
    return "0 (or failed to parse)"

def main():
    print("================================================================")
    print("            Matrix Scroll Adoption Instrumentation")
    print("================================================================")
    print("")

    token = os.environ.get("GITHUB_TOKEN")
    
    print("[*] Querying PyPI download statistics...")
    pypi = get_pypi_stats()
    if pypi:
        print(f"    - Downloads (Last Day):   {pypi.get('last_day', 0)}")
        print(f"    - Downloads (Last Week):  {pypi.get('last_week', 0)}")
        print(f"    - Downloads (Last Month): {pypi.get('last_month', 0)}")
    else:
        print("    - Error fetching PyPI statistics.")

    print("\n[*] Querying GitHub repository statistics...")
    gh = get_github_stats(token)
    print(f"    - CLI/SDK Stars:          {gh['repo_stars']}")
    print(f"    - CLI/SDK Forks:          {gh['repo_forks']}")
    print(f"    - Verify Action Stars:    {gh['action_stars']}")
    print(f"    - Verify Action Forks:    {gh['action_forks']}")
    print(f"    - Unique Clones (14d):    {gh['clones_14d']}")
    print(f"    - Unique Views (14d):     {gh['views_14d']}")

    print("\n[*] Querying Glama registry status...")
    glama_status = get_glama_registry_status()
    if "error" in glama_status:
        print(f"    - Error: {glama_status['error']}")
    else:
        print(f"    - matrixscroll quality:   {glama_status.get('matrixscroll_quality', 'unknown')}")
        print(f"    - matrixscroll license:   {glama_status.get('matrixscroll_license', 'unknown')}")
        print(f"    - matrixscroll maint.:    {glama_status.get('matrixscroll_maintenance', 'unknown')}")
        if glama_status.get("digital_rain_listed"):
            print("    - digital-rain-mcp:       STILL LISTED (email support@glama.ai, id xwxknl3sgw)")
        else:
            print("    - digital-rain-mcp:       not listed (ok)")

    print("\n[*] Querying Glama Registry favorites...")
    glama = get_glama_favorites()
    print(f"    - Glama Favorites:        {glama}")

    print("\n================================================================")
    print("  Report generated successfully.")
    print("================================================================")

if __name__ == "__main__":
    main()
