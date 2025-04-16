import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import json
from pathlib import Path

class WikiScraper:
    def __init__(self, base_url="https://en.wikipedia.org/wiki/Kenya"):
        self.base_url = base_url

    def fetch_page(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def get_toc_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all('a', class_="vector-toc-link")

    def scrape_content(self, output_file='kenya.txt', max_links=1):
        html = self.fetch_page(self.base_url)
        if not html:
            return False

        links = self.get_toc_links(html)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for link in links[:max_links]:
                    href = link.get('href')
                    if href and href.startswith('#'):
                        url = self.base_url + href
                        content = self.fetch_page(url)
                        if content:
                            soup = BeautifulSoup(content, 'html.parser')
                            # Extract only the content within the main body of the section
                            main_content = soup.find(id=href[1:])
                            if main_content:
                                text = main_content.get_text(separator='\n', strip=True)
                                print(f"Scraping section: {url}")
                                f.write(text + "\n\n")
            return True
        except IOError as e:
            print(f"Error writing to file: {e}")
            return False

class TextSummarizer:
    def __init__(self, model_name="facebook/bart-large-cnn"):
        self.summarizer = pipeline("summarization", model=model_name)

    def summarize_file(self, filepath, max_length=150, min_length=30):
        try:
            content = Path(filepath).read_text(encoding='utf-8')
        except Exception as e:
            return {"error": f"Error reading file: {e}"}

        if filepath.lower().endswith(('.html', '.htm')):
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
        else:
            text = content

        try:
            summary = self.summarizer(text,
                                     max_length=max_length,
                                     min_length=min_length,
                                     do_sample=False)[0]['summary_text']
            return {
                "original_filename": Path(filepath).name,
                "summary": summary
            }
        except Exception as e:
            return {"error": f"Error during summarization: {e}"}

def main():
    # Scrape Wikipedia content
    scraper = WikiScraper()
    scraper.scrape_content()

    # Summarize the content
    summarizer = TextSummarizer()
    summary_json = summarizer.summarize_file("kenya.txt")
    print(json.dumps(summary_json, indent=4))

if __name__ == "__main__":
    main()