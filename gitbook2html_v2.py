import requests
from bs4 import BeautifulSoup
import os
import time

# Function to fetch the main index of the GitBook and gather all page URLs
def fetch_all_page_urls(gitbook_url):
    response = requests.get(gitbook_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the links from the table of contents or summary (adjust this depending on the structure)
        toc_links = soup.select('a[href]')
        page_urls = []
        for link in toc_links:
            page_url = link['href']
            if page_url.startswith('/'):
                page_url = gitbook_url.rstrip('/') + page_url
            if gitbook_url in page_url:  # Only add valid GitBook pages
                page_urls.append(page_url)
        
        return page_urls
    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return []

# Function to fetch content from a GitBook page with a timeout
def fetch_gitbook_content(url, timeout=180):
    try:
        # Start measuring time
        start_time = time.time()
        
        # Make request with timeout
        response = requests.get(url, timeout=timeout)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Measure time spent on this request
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print(f"Warning: Page took longer than {timeout} seconds to load.")
                return "", ""
            
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the title
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else "GitBook Document"

            # Extract content (try multiple potential content structures)
            content_div = soup.find('div', class_='book-body') or \
                          soup.find('section') or \
                          soup.find('article') or \
                          soup.find('main')  # Add more checks based on your GitBook structure

            if content_div:
                # Remove unwanted elements:
                # 1. Remove all <a> tags (hyperlinks)
                for a_tag in content_div.find_all('a'):
                    a_tag.decompose()  # Completely remove the <a> tag and its contents
                for button_tag in content_div.find_all('button'):
                    button_tag.decompose()  # Удалить все кнопки

                # 2. Remove "Last updated" information (assuming it's in a div with a certain class or structure)
                last_updated_tag = content_div.find(text="Last updated")
                if last_updated_tag:
                    last_updated_tag.find_parent().decompose()  # Remove the parent element

                # 3. Remove "Was this helpful?" section (assuming it's in a div with a certain class)
                helpful_tag = content_div.find(text="Was this helpful?")
                if helpful_tag:
                    helpful_tag.find_parent().decompose()  # Remove the parent element

                # 4. Remove quality rating emojis or similar elements (assuming they have specific classes)
                quality_tags = content_div.find_all(class_="emoji")  # Replace with actual class for quality emoji
                for tag in quality_tags:
                    tag.decompose()  # Remove the tag

                # Clean the content of HTML tags
                text_content = content_div.get_text(strip=True)

                # Check if the content has less than 200 characters
                if len(text_content) < 200:
                    print(f"Page {url} skipped due to insufficient content.")
                    return title, ""  # Return empty content if it's too short

                return title, str(content_div)
            else:
                print(f"Could not find content on the page {url}.")
                return title, ""
        else:
            print(f"Failed to fetch the page {url}. Status code: {response.status_code}")
            return "", ""
    except requests.exceptions.Timeout:
        print(f"Error: The request to {url} timed out after {timeout} seconds.")
        return "", ""

# Function to save HTML content to a file
def save_html_content(html_content, output_html):
    with open(output_html, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"HTML saved to {output_html}")

# Main function to fetch and save all GitBook pages as HTML
def gitbook_to_html(gitbook_url, output_html):
    # Fetch all page URLs
    page_urls = fetch_all_page_urls(gitbook_url)

    if not page_urls:
        print("No pages found to convert.")
        return

    print(f"Found {len(page_urls)} pages to convert.")

    # Fetch content for each page
    full_content = ""
    for i, page_url in enumerate(page_urls):
        title, content = fetch_gitbook_content(page_url)
        if content:
            full_content += f"<h1>{title}</h1>{content}"
        else:
            print(f"Warning: Content for page {page_url} could not be fetched or was empty.")
        print(f"Fetched and added content from page {i+1}/{len(page_urls)}: {page_url}")

    # Generate full HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{gitbook_url} - GitBook HTML</title>
    </head>
    <body>
        {full_content}
    </body>
    </html>
    """

    # Save HTML content to a file
    save_html_content(html_content, output_html)

# Ensure output folder exists
if not os.path.exists('output'):
    os.makedirs('output')

# URL of the GitBook page
gitbook_url = "https://kb.pvhostvm.ru/"  # Replace with the actual GitBook URL

# Output HTML file path
output_html = "output/copied_gitbook.html"

# Run the conversion
gitbook_to_html(gitbook_url, output_html)
