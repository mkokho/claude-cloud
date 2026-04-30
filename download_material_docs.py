#!/usr/bin/env python3
"""
Script to download text content from Material Design documentation.
Preserves text content and image links.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
from pathlib import Path


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

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    content_lines = []

    # Process the main content
    main_content = soup.find('main') or soup.find('article') or soup.body

    if main_content:
        for element in main_content.find_all(recursive=True):
            # Handle images
            if element.name == 'img':
                img_src = element.get('src', '')
                img_alt = element.get('alt', 'Image')
                if img_src:
                    full_url = urljoin(base_url, img_src)
                    content_lines.append(f"\n[IMAGE: {img_alt}]\n{full_url}\n")

            # Handle headings
            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if element.parent.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = element.get_text(strip=True)
                    if text:
                        content_lines.append(f"\n{text}\n")

            # Handle paragraphs
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text and element.parent.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    content_lines.append(text)

            # Handle lists
            elif element.name in ['li']:
                text = element.get_text(strip=True)
                if text and not any(parent.name in ['ul', 'ol']
                                   for parent in element.parents
                                   if parent.name):
                    content_lines.append(f"  • {text}")

            # Handle links with text
            elif element.name == 'a':
                text = element.get_text(strip=True)
                href = element.get('href', '')
                if text and not any(parent.name in ['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                                   for parent in element.parents):
                    if href:
                        full_url = urljoin(base_url, href)
                        content_lines.append(f"[LINK: {text}] {full_url}")

    # Join content and clean up excessive whitespace
    text = '\n'.join(content_lines)

    # Clean up multiple consecutive newlines
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')

    return text.strip()


def download_material_docs(url, output_file='material_design_docs.txt'):
    """
    Download and extract text from Material Design documentation.

    Args:
        url: URL to download from
        output_file: Output file path
    """
    print(f"Downloading from {url}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Status: {response.status_code}")

        content = extract_text_and_images(response.content, url)

        # Save to file
        Path(output_file).write_text(content, encoding='utf-8')
        print(f"✓ Downloaded content saved to {output_file}")
        print(f"✓ File size: {len(content)} characters")

        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Error downloading: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    url = 'https://m3.material.io/get-started'
    output_file = 'material_design_docs.txt'

    if len(sys.argv) > 1:
        url = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    success = download_material_docs(url, output_file)
    sys.exit(0 if success else 1)
