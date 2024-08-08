
import requests

def addPretext(lines, sectionName, baseURL, subURL):
    modified_lines = []
    currMdSubheading = ""
    currSubCat = ""
    currSubSubCat = ""

    #Remove from the lines any line that isnt a heading and doesnt contain the character `⭐`
    #lines = [line for line in lines if line.startswith("#") or '⭐' in line]

    #Parse headings
    for line in lines:
        if line.startswith("#"): #Title Lines
            if not subURL=="storage":
                if line.startswith("# ►"):
                    currMdSubheading = "#" + line.replace("# ►", "").strip().replace(" / ", "-").replace(" ", "-").lower()
                    currSubCat = line.replace("# ►", "").strip()
                    currSubSubCat = "/"
                elif line.startswith("## ▷"):
                    if not subURL=="non-english": #Because non-eng section has multiple subsubcats with same names
                        currMdSubheading = "#" + line.replace("## ▷", "").strip().replace(" / ", "-").replace(" ", "-").lower()
                    currSubSubCat = line.replace("## ▷", "").strip()
            elif subURL=="storage":
                if line.startswith("## "):
                    currMdSubheading = "#" + line.replace("## ", "").strip().replace(" / ", "-").replace(" ", "-").lower()
                    currSubCat = line.replace("## ", "").strip()
                    currSubSubCat = "/"
                elif line.startswith("### "):
                    currMdSubheading = "#" + line.replace("### ", "").strip().replace(" / ", "-").replace(" ", "-").lower()
                    currSubSubCat = line.replace("### ", "").strip()

            # Remove links from subcategory titles (because the screw the format)
            if 'http' in currSubCat: currSubCat = ''
            if 'http' in currSubSubCat: currSubSubCat = ''

        elif any(char.isalpha() for char in line): #If line has content
            preText = f"{{\"{sectionName.replace(".md", "")}\", \"{currSubCat}\", \"{currSubSubCat}\"}}"
            if line.startswith("* "): line = line[2:]
            modified_lines.append(preText + line)

    return modified_lines


#----------------base64 page processing------------
import base64
import re

doBase64Decoding = True

def fix_base64_string(encoded_string):
    missing_padding = len(encoded_string) % 4
    if missing_padding != 0:
        encoded_string += '=' * (4 - missing_padding)
    return encoded_string

def decode_base64_in_backticks(input_string):
    def base64_decode(match):
        encoded_data = match.group(0)[1:-1]  # Extract content within backticks
        decoded_bytes = base64.b64decode( fix_base64_string(encoded_data) )
        return decoded_bytes.decode()

    pattern = r"`[^`]+`"  # Regex pattern to find substrings within backticks
    decoded_string = re.sub(pattern, base64_decode, input_string)
    return decoded_string

def remove_empty_lines(text):
    lines = text.split('\n')  # Split the text into lines
    non_empty_lines = [line for line in lines if line.strip()]  # Filter out empty lines
    return '\n'.join(non_empty_lines)  # Join non-empty lines back together

def extract_base64_sections(base64_page):
    sections = base64_page.split("***")  # Split the input string by "***" to get sections
    formatted_sections = []
    for section in sections:
        formatted_section = remove_empty_lines( section.strip().replace("#### ", "").replace("\n\n", " - ").replace("\n", ", ") )
        if doBase64Decoding: formatted_section = decode_base64_in_backticks(formatted_section)
        formatted_section = '[🔑Base64](https://rentry.co/FMHYBase64) ► ' + formatted_section
        formatted_sections.append(formatted_section)
    lines = formatted_sections
    return lines
#----------------</end>base64 page processing------------



def dlWikiChunk(fileName, icon, redditSubURL):

    #first, try to get the chunk locally
    try:
        #First, try to get it from the local file
        print("Loading " + fileName + " from local file...")
        with open(fileName.lower(), 'r') as f:
            page = f.read()
        print("Loaded.\n")
    #if not available locally, download the chunk
    except:
        if not fileName=='base64.md':
            print("Local file not found. Downloading " + fileName + " from Github...")
            page = requests.get("https://raw.githubusercontent.com/fmhy/FMHYedit/main/docs/" + fileName.lower()).text
        elif fileName=='base64.md':
            print("Local file not found. Downloading rentry.co/FMHYBase64...")
            page = requests.get("https://rentry.co/FMHYBase64/raw").text.replace("\r", "")
        print("Downloaded")

    #add a pretext
    redditBaseURL = "https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/"
    siteBaseURL = "https://fmhy.net/"
    if not fileName=='base64.md':
        pagesDevSiteSubURL = fileName.replace(".md", "").lower()
        subURL = pagesDevSiteSubURL
        lines = page.split('\n')
        lines = addPretext(lines, fileName, siteBaseURL, subURL)
    elif fileName=='base64.md':
        lines = extract_base64_sections(page)

    return lines

def cleanLineForSearchMatchChecks(line):
    siteBaseURL = "https://fmhy.net/"
    redditBaseURL = "https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/"
    return line.replace(redditBaseURL, '/').replace(siteBaseURL, '/')

def alternativeWikiIndexing():
    wikiChunks = [
        dlWikiChunk("VideoPiracyGuide.md", "📺", "video"),
        dlWikiChunk("AI.md", "🤖", "ai"),
        dlWikiChunk("Android-iOSGuide.md", "📱", "android"),
        dlWikiChunk("AudioPiracyGuide.md", "🎵", "audio"),
        dlWikiChunk("DownloadPiracyGuide.md", "💾", "download"),
        dlWikiChunk("EDUPiracyGuide.md", "🧠", "edu"),
        dlWikiChunk("GamingPiracyGuide.md", "🎮", "games"),
        dlWikiChunk("AdblockVPNGuide.md", "📛", "adblock-vpn-privacy"),
        dlWikiChunk("System-Tools.md", "💻", "system-tools"),
        dlWikiChunk("File-Tools.md", "🗃️", "file-tools"),
        dlWikiChunk("Internet-Tools.md", "🔗", "internet-tools"),
        dlWikiChunk("Social-Media-Tools.md", "💬", "social-media"),
        dlWikiChunk("Text-Tools.md", "📝", "text-tools"),
        dlWikiChunk("Video-Tools.md", "📼", "video-tools"),
        dlWikiChunk("MISCGuide.md", "📂", "misc"),
        dlWikiChunk("ReadingPiracyGuide.md", "📗", "reading"),
        dlWikiChunk("TorrentPiracyGuide.md", "🌀", "torrent"),
        dlWikiChunk("img-tools.md", "📷", "img-tools"),
        dlWikiChunk("gaming-tools.md", "👾", "gaming-tools"),
        dlWikiChunk("LinuxGuide.md", "🐧🍏", "linux"),
        dlWikiChunk("DEVTools.md", "🖥️", "dev-tools"),
        dlWikiChunk("Non-English.md", "🌏", "non-eng"),
        dlWikiChunk("STORAGE.md", "🗄️", "storage"),
        #dlWikiChunk("base64.md", "🔑", "base64"),
        dlWikiChunk("NSFWPiracy.md", "🌶", "https://saidit.net/s/freemediafuckyeah/wiki/index")
    ]
    return [item for sublist in wikiChunks for item in sublist] #Flatten a <list of lists of strings> into a <list of strings>
#--------------------------------


# Save the result of alternativeWikiIndexing to a .md file
# with open('wiki_adapted.md', 'w') as f:
#     for line in alternativeWikiIndexing():
#         f.write(line + '\n')

# Instead of saving it to a file, save it into a string variable
wiki_adapted_md = '\n'.join(alternativeWikiIndexing())

# Remove from the lines in wiki_adapted_md any line that doesnt contain the character `⭐`
wiki_adapted_starred_only_md = '\n'.join([line for line in wiki_adapted_md.split('\n') if '⭐' in line])



import re

def markdown_to_html_bookmarks(input_md_text, output_file):
    # Predefined folder name
    folder_name = "FMHY"
    
    # Read the input markdown file
    #with open(input_file, 'r', encoding='utf-8') as f:
    #    markdown_content = f.read()

    # Instead of reading from a file, read from a string variable
    markdown_content = input_md_text
    
    # Regex pattern to extract URLs and titles from markdown
    url_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
    # Regex pattern to extract hierarchy levels
    hierarchy_pattern = re.compile(r'^\{"([^"]+)", "([^"]+)", "([^"]+)"\}')
    
    # Dictionary to hold bookmarks by hierarchy
    bookmarks = {}
    
    # Split the content by lines
    lines = markdown_content.split('\n')
    
    # Parse each line
    for line in lines:
        # Find hierarchy levels
        hierarchy_match = hierarchy_pattern.match(line)
        if not hierarchy_match:
            continue

        level1, level2, level3 = hierarchy_match.groups()
        
        # Initialize nested dictionaries for hierarchy levels
        if level1 not in bookmarks:
            bookmarks[level1] = {}
        if level2 not in bookmarks[level1]:
            bookmarks[level1][level2] = {}
        if level3 not in bookmarks[level1][level2]:
            bookmarks[level1][level2][level3] = []

        # Find all matches in the line for URLs
        matches = url_pattern.findall(line)

        # If the input_md_text is wiki_adapted_starred_only_md, only add the first match of url_pattern in each line
        if input_md_text == wiki_adapted_starred_only_md:
            matches = matches[:1]
        
        # Extract the description (text after the last match)
        last_match_end = line.rfind(')')
        description = line[last_match_end+1:].replace('**', '').strip() if last_match_end != -1 else ''
        
        # When the description is empty, use as description the lowest hierachy level that is not empty
        if not description:
            description = '- ' + (level3 if level3 != '/' else level2 if level2 else level1)

        # Add matches to the appropriate hierarchy
        for title, url in matches:
            full_title = f"{title} {description}" if description else title
            bookmarks[level1][level2][level3].append((full_title, url))
    
    # Function to generate HTML from nested dictionary
    def generate_html(bookmarks_dict, indent=1):
        html = ''
        for key, value in bookmarks_dict.items():
            html += '    ' * indent + f'<DT><H3>{key}</H3>\n'
            html += '    ' * indent + '<DL><p>\n'
            if isinstance(value, dict):
                html += generate_html(value, indent + 1)
            else:
                for full_title, url in value:
                    html += '    ' * (indent + 1) + f'<DT><A HREF="{url}" ADD_DATE="0">{full_title}</A>\n'
            html += '    ' * indent + '</DL><p>\n'
        return html
    
    # HTML structure
    html_content = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
'''
    # Add the main folder
    html_content += f'    <DT><H3>{folder_name}</H3>\n'
    html_content += '    <DL><p>\n'
    
    # Add bookmarks to HTML content
    html_content += generate_html(bookmarks)
    
    html_content += '    </DL><p>\n'
    html_content += '</DL><p>\n'
    
    # Write the HTML content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Print success message
    #print(f'Successfully created bookmarks in {output_file}')

# Example usage:
markdown_to_html_bookmarks(wiki_adapted_md, 'fmhy_in_bookmarks.html')
markdown_to_html_bookmarks(wiki_adapted_starred_only_md, 'fmhy_in_bookmarks_starred_only.html')
