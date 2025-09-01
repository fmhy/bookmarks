"""Generate FMHY bookmark HTML files from FMHY markdown sections."""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    """Configuration constants for the FMHY bookmark generator."""

    site_base_url: str = "https://fmhy.net/"
    reddit_base_url: str = "https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/"
    base64_rentry_url: str = "https://rentry.co/FMHYBase64/raw"
    github_raw_base: str = (
        "https://raw.githubusercontent.com/fmhy/edit/refs/heads/main/docs/"
    )
    folder_name: str = "FMHY"
    decode_base64: bool = True


@dataclass
class WikiSection:
    """Represents a wiki section to be processed."""

    filename: str
    icon: str
    url_key: str


CONFIG = Config()


def parse_heading(line: str, sub_url: str) -> Tuple[str, str]:
    """Parse heading line and return (subcategory, subsubcategory)."""
    if sub_url != "storage":
        if line.startswith("# ►"):
            return line.replace("# ►", "").strip(), "/"
        elif line.startswith("## ▷"):
            return "", line.replace("## ▷", "").strip()
    else:  # storage section uses different heading levels
        if line.startswith("## "):
            return line.replace("## ", "").strip(), "/"
        elif line.startswith("### "):
            return "", line.replace("### ", "").strip()
    return "", ""


def clean_category_name(category: str) -> str:
    """Remove URLs from category names."""
    return "" if "http" in category else category


def add_hierarchy_prefix(
    lines: List[str], section_name: str, sub_url: str
) -> List[str]:
    """Add hierarchy prefix to content lines."""
    modified_lines = []
    curr_subcat = ""
    curr_subsubcat = ""

    for line in lines:
        if line.startswith("#"):  # Heading line
            subcat, subsubcat = parse_heading(line, sub_url)
            if subcat:
                curr_subcat = clean_category_name(subcat)
            if subsubcat:
                curr_subsubcat = clean_category_name(subsubcat)
        elif any(char.isalpha() for char in line):  # Content line
            prefix = f'{{"{section_name.replace(".md", "")}", "{curr_subcat}", "{curr_subsubcat}"}}'
            content = line[2:] if line.startswith("* ") else line
            modified_lines.append(prefix + content)

    return modified_lines


# Base64 processing functions
def fix_base64_padding(encoded_string: str) -> str:
    """Fix base64 padding."""
    missing_padding = len(encoded_string) % 4
    if missing_padding:
        encoded_string += "=" * (4 - missing_padding)
    return encoded_string


def decode_base64_content(input_string: str) -> str:
    """Decode base64 content within backticks."""
    if not CONFIG.decode_base64:
        return input_string

    def base64_decode(match):
        encoded_data = match.group(0)[1:-1]  # Remove backticks
        decoded_bytes = base64.b64decode(fix_base64_padding(encoded_data))
        return decoded_bytes.decode()

    pattern = r"`[^`]+`"
    return re.sub(pattern, base64_decode, input_string)


def process_base64_sections(base64_page: str) -> List[str]:
    """Process base64 page sections."""
    sections = base64_page.split("***")
    formatted_sections = []

    for section in sections:
        # Clean up section formatting
        clean_section = (
            section.strip()
            .replace("#### ", "")
            .replace("\n\n", " - ")
            .replace("\n", ", ")
        )

        # Remove empty lines
        lines = [line for line in clean_section.split("\n") if line.strip()]
        clean_section = "\n".join(lines)

        # Decode base64 if enabled
        clean_section = decode_base64_content(clean_section)

        # Add base64 prefix
        formatted_section = (
            "[🔑Base64](https://rentry.co/FMHYBase64) ► " + clean_section
        )
        formatted_sections.append(formatted_section)

    return formatted_sections


def download_wiki_content(filename: str) -> List[str]:
    """Download and process wiki content."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info("Loaded %s locally", filename)
    except FileNotFoundError:
        if filename != "base64.md":
            url = CONFIG.github_raw_base + filename
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                content = resp.text
                logger.info("Downloaded %s", filename)
            except requests.HTTPError as e:
                logger.error("Failed to fetch %s (%s). Skipping.", filename, e)
                return []
        else:
            logger.info("Downloading Base64 page from rentry...")
            resp = requests.get(CONFIG.base64_rentry_url, timeout=30)
            resp.raise_for_status()
            content = resp.text.replace("\r", "")
            logger.info("Downloaded base64 page")

    if filename != "base64.md":
        sub_url = filename.replace(".md", "").lower()
        return add_hierarchy_prefix(content.split("\n"), filename, sub_url)
    else:
        return process_base64_sections(content)


# Wiki sections to process
WIKI_SECTIONS = [
    WikiSection("video.md", "📺", "video"),
    WikiSection("ai.md", "🤖", "ai"),
    WikiSection("mobile.md", "📱", "mobile"),
    WikiSection("audio.md", "🎵", "audio"),
    WikiSection("downloading.md", "💾", "downloading"),
    WikiSection("educational.md", "🧠", "educational"),
    WikiSection("gaming.md", "🎮", "gaming"),
    WikiSection("privacy.md", "📛", "privacy"),
    WikiSection("system-tools.md", "💻", "system-tools"),
    WikiSection("file-tools.md", "🗃️", "file-tools"),
    WikiSection("internet-tools.md", "🔗", "internet-tools"),
    WikiSection("social-media-tools.md", "💬", "social-media-tools"),
    WikiSection("text-tools.md", "📝", "text-tools"),
    WikiSection("video-tools.md", "📼", "video-tools"),
    WikiSection("misc.md", "📂", "misc"),
    WikiSection("reading.md", "📗", "reading"),
    WikiSection("torrenting.md", "🌀", "torrenting"),
    WikiSection("image-tools.md", "📷", "image-tools"),
    WikiSection("gaming-tools.md", "👾", "gaming-tools"),
    WikiSection("linux-macos.md", "🐧🍏", "linux-macos"),
    WikiSection("developer-tools.md", "🖥️", "developer-tools"),
    WikiSection("non-english.md", "🌏", "non-english"),
    WikiSection("storage.md", "🗄️", "storage"),
    WikiSection("base64.md", "🔑", "base64"),
    WikiSection("unsafe.md", "🌶", "unsafe"),
]


def collect_all_wiki_content() -> List[str]:
    """Collect and process all wiki sections."""
    all_lines = []
    for section in WIKI_SECTIONS:
        lines = download_wiki_content(section.filename)
        all_lines.extend(lines)
    return all_lines


def filter_starred_content(content: str) -> str:
    """Filter content to only include starred items."""
    return "\n".join(
        line for line in content.split("\n") if "⭐" in line or "🌟" in line
    )


def parse_bookmark_line(
    line: str, starred_only: bool = False
) -> Tuple[str, str, str, List[Tuple[str, str]]]:
    """Parse a line to extract hierarchy and bookmarks."""
    url_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
    hierarchy_pattern = re.compile(r'^\{"([^"]+)", "([^"]+)", "([^"]+)"\}')

    hierarchy_match = hierarchy_pattern.match(line)
    if not hierarchy_match:
        return "", "", "", []

    level1, level2, level3 = hierarchy_match.groups()
    matches = url_pattern.findall(line)

    if starred_only:
        matches = matches[:1]  # Only first match for starred content

    # Extract description (text after last URL)
    last_paren = line.rfind(")")
    description = (
        line[last_paren + 1 :].replace("**", "").strip() if last_paren != -1 else ""
    )

    if not description:
        description = "- " + (level3 if level3 != "/" else level2 if level2 else level1)

    bookmarks = [(f"{title} {description}".strip(), url) for title, url in matches]
    return level1, level2, level3, bookmarks


def generate_bookmark_html(bookmarks_dict: Dict, indent: int = 1) -> str:
    """Generate HTML from bookmark dictionary."""
    html = ""
    for key, value in bookmarks_dict.items():
        html += "    " * indent + f"<DT><H3>{key}</H3>\n"
        html += "    " * indent + "<DL><p>\n"

        if isinstance(value, dict):
            html += generate_bookmark_html(value, indent + 1)
        else:
            for title, url in value:
                html += (
                    "    " * (indent + 1)
                    + f'<DT><A HREF="{url}" ADD_DATE="0">{title}</A>\n'
                )

        html += "    " * indent + "</DL><p>\n"
    return html


def create_html_bookmarks(
    content: str, output_file: str, starred_only: bool = False
) -> None:
    """Create HTML bookmark file from processed content."""
    bookmarks: Dict[str, Dict[str, Dict[str, List[Tuple[str, str]]]]] = {}

    for line in content.split("\n"):
        level1, level2, level3, bookmark_list = parse_bookmark_line(line, starred_only)
        if not level1:  # Skip lines that don't match hierarchy pattern
            continue

        # Initialize nested structure
        bookmarks.setdefault(level1, {}).setdefault(level2, {}).setdefault(level3, [])
        bookmarks[level1][level2][level3].extend(bookmark_list)

    # Generate HTML
    html_content = (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
        "<TITLE>Bookmarks</TITLE>\n"
        "<H1>Bookmarks</H1>\n"
        "<DL><p>\n"
        f"    <DT><H3>{CONFIG.folder_name}</H3>\n"
        "    <DL><p>\n" + generate_bookmark_html(bookmarks) + "    </DL><p>\n"
        "</DL><p>\n"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("Created bookmark file: %s", output_file)


def main() -> None:
    """Main execution function."""
    logger.info("Collecting wiki content...")
    all_content = collect_all_wiki_content()
    full_content = "\n".join(all_content)

    # Generate both bookmark files
    create_html_bookmarks(full_content, "fmhy_in_bookmarks.html")

    starred_content = filter_starred_content(full_content)
    create_html_bookmarks(
        starred_content, "fmhy_in_bookmarks_starred_only.html", starred_only=True
    )

    logger.info("Bookmark generation complete!")


if __name__ == "__main__":
    main()
