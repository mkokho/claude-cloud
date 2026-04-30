#!/usr/bin/env python3
"""
Script to download text content from Material Design documentation using sitemap.
Crawls all pages listed in sitemap and extracts text content with image links.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict


def get_urls_from_sitemap(sitemap_url):
    """
    Parse sitemap and extract all URLs.

    Args:
        sitemap_url: URL to the sitemap.xml

    Returns:
        List of URLs
    """
    print(f"Fetching sitemap: {sitemap_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        urls = []

        # Handle sitemap namespace
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_elem in root.findall('ns:url', ns):
            loc = url_elem.find('ns:loc', ns)
            if loc is not None:
                urls.append(loc.text)

        # Fallback if no namespace
        if not urls:
            for url_elem in root.findall('url'):
                loc = url_elem.find('loc')
                if loc is not None:
                    urls.append(loc.text)

        print(f"Found {len(urls)} URLs in sitemap")
        return urls

    except Exception as e:
        print(f"✗ Error parsing sitemap: {e}", file=sys.stderr)
        return []


def extract_text_and_images(html_content, base_url):
    """
    Extract text content and image links from HTML.

    Args:
        html_content: HTML string
        base_url: Base URL for resolving relative links

    Returns:
        String with extracted content
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title
    title = ''
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Remove script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    content_lines = []
    if title:
        content_lines.append(title)

    # Collect all images
    images = []
    for img in soup.find_all('img'):
        img_src = img.get('src', '')
        img_alt = img.get('alt', '')
        if img_src:
            full_url = urljoin(base_url, img_src)
            images.append((img_alt, full_url))

    # Extract text from main content area
    main_content = soup.find('main') or soup.find('article') or soup.body
    if main_content:
        text = main_content.get_text(separator='\n', strip=True)
        if text:
            content_lines.append(text)

    # Add images section if found
    if images:
        content_lines.append("\n[IMAGES]\n")
        for alt, url in images:
            if alt:
                content_lines.append(f"  {alt}: {url}")
            else:
                content_lines.append(f"  {url}")

    # Join content
    text = '\n'.join(content_lines)

    # Clean up multiple consecutive newlines
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')

    return text.strip()


def download_page(url, headers=None):
    """
    Download a single page and extract text.

    Args:
        url: URL to download
        headers: HTTP headers

    Returns:
        Tuple of (success, content, url_path)
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        content = extract_text_and_images(response.content, url)
        return True, content, urlparse(url).path or '/'

    except Exception as e:
        print(f"  ✗ Failed: {url} - {e}", file=sys.stderr)
        return False, '', ''


def download_material_docs(sitemap_url, output_file='material_design_docs.txt'):
    """
    Download and extract text from entire Material Design documentation using sitemap.

    Args:
        sitemap_url: URL to the sitemap.xml
        output_file: Output file path
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Get URLs from sitemap
    urls = get_urls_from_sitemap(sitemap_url)
    if not urls:
        print("✗ No URLs found in sitemap", file=sys.stderr)
        return False

    all_content = []
    successful = 0
    failed = 0

    print(f"\nDownloading {len(urls)} pages...")

    for i, url in enumerate(urls, 1):
        print(f"  [{i}/{len(urls)}] {url}")
        success, content, path = download_page(url, headers)

        if success and content:
            all_content.append(f"\n{'='*80}")
            all_content.append(f"URL: {url}")
            all_content.append(f"{'='*80}\n")
            all_content.append(content)
            successful += 1
        else:
            failed += 1

    # Save combined content
    final_content = '\n'.join(all_content)
    Path(output_file).write_text(final_content, encoding='utf-8')

    print(f"\n✓ Downloaded {successful}/{len(urls)} pages")
    print(f"✓ Content saved to {output_file}")
    print(f"✓ File size: {len(final_content)} characters")

    return True


if __name__ == '__main__':
    sitemap_url = 'https://m3.material.io/sitemap.xml'
    output_file = 'material_design_docs.txt'

    if len(sys.argv) > 1:
        sitemap_url = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    success = download_material_docs(sitemap_url, output_file)
    sys.exit(0 if success else 1)
