"""Generate FMHY bookmark HTML files from FMHY markdown sections."""

from __future__ import annotations

import asyncio
import base64
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import aiohttp

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
class BookmarkLine:
    """Represents one original content line at a leaf."""

    is_starred: bool  # line contains ⭐ or 🌟
    description_raw: str  # raw trailing text after last ")", may be empty
    links: List[Tuple[str, str]]  # list of (title, url) exactly as matched


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


async def download_wiki_content_async(
    session: aiohttp.ClientSession, filename: str
) -> Tuple[str, List[str]]:
    """Download and process wiki content asynchronously."""
    # First try to load locally
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info("Loaded %s locally", filename)

        if filename != "base64.md":
            sub_url = filename.replace(".md", "").lower()
            return filename, add_hierarchy_prefix(
                content.split("\n"), filename, sub_url
            )
        else:
            return filename, process_base64_sections(content)
    except FileNotFoundError:
        pass

    # Download remotely if not found locally
    try:
        if filename != "base64.md":
            url = CONFIG.github_raw_base + filename
        else:
            url = CONFIG.base64_rentry_url

        async with session.get(url, timeout=30) as resp:
            resp.raise_for_status()
            content = await resp.text()

            if filename == "base64.md":
                content = content.replace("\r", "")
                logger.info("Downloaded base64 page")
                return filename, process_base64_sections(content)
            else:
                logger.info("Downloaded %s", filename)
                sub_url = filename.replace(".md", "").lower()
                return filename, add_hierarchy_prefix(
                    content.split("\n"), filename, sub_url
                )

    except Exception as e:
        logger.error("Failed to fetch %s (%s). Skipping.", filename, e)
        return filename, []


async def collect_all_wiki_content_async() -> List[str]:
    """Collect and process all wiki sections concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for section in WIKI_SECTIONS:
            task = download_wiki_content_async(session, section.filename)
            tasks.append(task)

        logger.info("Starting concurrent fetching of %d sections...", len(tasks))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_lines = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Download task failed: %s", result)
                continue
            filename, lines = result
            all_lines.extend(lines)

        return all_lines


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


async def main_async() -> None:
    """Main execution function (async version)."""
    logger.info("Collecting wiki content...")
    all_content = await collect_all_wiki_content_async()
    full_content = "\n".join(all_content)

    # Generate both bookmark files
    create_html_bookmarks(full_content, "fmhy_in_bookmarks.html")
    create_html_bookmarks(
        full_content, "fmhy_in_bookmarks_starred_only.html", starred_only=True
    )

    logger.info("Bookmark generation complete!")


def parse_bookmark_line(line: str) -> Tuple[str, str, str, BookmarkLine | None]:
    """Parse a line to extract hierarchy and bookmark data."""
    url_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
    hierarchy_pattern = re.compile(r'^\{"([^"]+)", "([^"]+)", "([^"]+)"\}')

    hierarchy_match = hierarchy_pattern.match(line)
    if not hierarchy_match:
        return "", "", "", None

    level1, level2, level3 = hierarchy_match.groups()
    matches = url_pattern.findall(line)

    # Remove non-primary Discord invites, X, Telegram and .onion links
    filters = {"Discord", "X", "Telegram", ".onion"}
    for matched_link in matches.copy():
        if matched_link[0] in filters:
            matches.remove(matched_link)

    # Check if line contains starred content
    is_starred = "⭐" in line or "🌟" in line

    # Extract raw description (text after last URL)
    last_paren = line.rfind(")")
    description_raw = (
        line[last_paren + 1 :].replace("**", "").strip() if last_paren != -1 else ""
    )

    bookmark_line = BookmarkLine(
        is_starred=is_starred, description_raw=description_raw, links=matches
    )

    return level1, level2, level3, bookmark_line


def generate_bookmark_html(
    bookmarks_dict: Dict[str, Dict[str, Dict[str, List[BookmarkLine]]]],
    indent: int = 1,
    starred_only: bool = False,
    path: Tuple[str, ...] = (),
) -> str:
    """Generate HTML from bookmark dictionary."""
    html = ""
    for key, value in bookmarks_dict.items():
        html += "    " * indent + f"<DT><H3>{key}</H3>\n"
        html += "    " * indent + "<DL><p>\n"

        current_path = path + (key,)

        if isinstance(value, dict):
            html += generate_bookmark_html(
                value, indent + 1, starred_only, current_path
            )
        else:
            # At leaf level - render BookmarkLine items
            # current_path should be (level1, level2, level3)
            level1, level2, level3 = (
                current_path if len(current_path) >= 3 else ("", "", "")
            )

            for bookmark_line in value:
                # Skip if starred_only mode and line is not starred
                if starred_only and not bookmark_line.is_starred:
                    continue

                # Compute effective description
                if bookmark_line.description_raw:
                    effective_description = bookmark_line.description_raw
                else:
                    # Fallback description using current hierarchy path
                    effective_description = "- " + (
                        level3 if level3 != "/" else level2 if level2 else level1
                    )

                # Determine which links to render
                links_to_render = bookmark_line.links
                if starred_only:
                    links_to_render = links_to_render[
                        :1
                    ]  # Only first link for starred content

                # Render each link
                for title, url in links_to_render:
                    anchor_text = f"{title} {effective_description}".strip()
                    html += (
                        "    " * (indent + 1)
                        + f'<DT><A HREF="{url}" ADD_DATE="0">{anchor_text}</A>\n'
                    )

        html += "    " * indent + "</DL><p>\n"
    return html


def create_html_bookmarks(
    content: str, output_file: str, starred_only: bool = False
) -> None:
    """Create HTML bookmark file from processed content."""
    bookmarks: Dict[str, Dict[str, Dict[str, List[BookmarkLine]]]] = {}

    for line in content.split("\n"):
        level1, level2, level3, bookmark_line = parse_bookmark_line(line)
        if (
            not level1 or bookmark_line is None
        ):  # Skip lines that don't match hierarchy pattern
            continue

        # Initialize nested structure
        bookmarks.setdefault(level1, {}).setdefault(level2, {}).setdefault(level3, [])
        bookmarks[level1][level2][level3].append(bookmark_line)

    # Generate HTML
    html_content = (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
        "<TITLE>Bookmarks</TITLE>\n"
        "<H1>Bookmarks</H1>\n"
        "<DL><p>\n"
        f"    <DT><H3>{CONFIG.folder_name}</H3>\n"
        "    <DL><p>\n"
        + generate_bookmark_html(bookmarks, indent=2, starred_only=starred_only)
        + "    </DL><p>\n"
        "</DL><p>\n"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("Created bookmark file: %s", output_file)


def main() -> None:
    """Main execution function."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
