import asyncio
from playwright.async_api import async_playwright
import json
import os
import random
import time
from datetime import datetime

async def scrape_kenya_data():
    # Check if existing data file exists to use as fallback
    fallback_data = {}
    if os.path.exists('kenya_data.json'):
        try:
            with open('kenya_data.json', 'r', encoding='utf-8') as f:
                fallback_data = json.load(f)
                print("Loaded existing data as fallback")
        except Exception as e:
            print(f"Warning: Could not load existing data file: {e}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Set a realistic user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Dictionary to store all scraped data
            kenya_data = {
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Scrape general information about Kenya from Wikipedia
            try:
                print("Scraping Wikipedia...")
                await page.goto('https://en.wikipedia.org/wiki/Kenya', {'timeout': 60000})
                
                # Add random delay to avoid detection
                await asyncio.sleep(random.uniform(2, 5))
                
                # Extract basic information
                country_name = await page.locator('h1#firstHeading').inner_text()
                kenya_data["country"] = country_name
                
                # Get the infobox data
                infobox = page.locator('.infobox')
                
                # Extract capital
                try:
                    capital_element = infobox.locator('th:has-text("Capital") + td')
                    kenya_data["capital"] = await capital_element.inner_text() if await capital_element.count() > 0 else fallback_data.get("capital", "Not found")
                except Exception as e:
                    print(f"Error extracting capital: {e}")
                    kenya_data["capital"] = fallback_data.get("capital", "Not found")
                
                # Extract official languages
                try:
                    languages_element = infobox.locator('th:has-text("Official languages") + td')
                    kenya_data["official_languages"] = await languages_element.inner_text() if await languages_element.count() > 0 else fallback_data.get("official_languages", "Not found")
                except Exception as e:
                    print(f"Error extracting languages: {e}")
                    kenya_data["official_languages"] = fallback_data.get("official_languages", "Not found")
                
                # Extract population
                try:
                    population_element = infobox.locator('th:has-text("Population") ~ tr th:has-text("2019 census") + td')
                    kenya_data["population"] = await population_element.inner_text() if await population_element.count() > 0 else fallback_data.get("population", "Not found")
                except Exception as e:
                    print(f"Error extracting population: {e}")
                    kenya_data["population"] = fallback_data.get("population", "Not found")
                
                # Extract area
                try:
                    area_element = infobox.locator('th:has-text("Area") ~ tr th:has-text("Total") + td')
                    kenya_data["area"] = await area_element.inner_text() if await area_element.count() > 0 else fallback_data.get("area", "Not found")
                except Exception as e:
                    print(f"Error extracting area: {e}")
                    kenya_data["area"] = fallback_data.get("area", "Not found")
                
                # Extract currency
                try:
                    currency_element = infobox.locator('th:has-text("Currency") + td')
                    kenya_data["currency"] = await currency_element.inner_text() if await currency_element.count() > 0 else fallback_data.get("currency", "Not found")
                except Exception as e:
                    print(f"Error extracting currency: {e}")
                    kenya_data["currency"] = fallback_data.get("currency", "Not found")
                
                # Extract introduction paragraph
                try:
                    intro_paragraphs = page.locator('.mw-parser-output > p')
                    intro_text = ""
                    for i in range(await intro_paragraphs.count()):
                        paragraph = await intro_paragraphs.nth(i).inner_text()
                        if len(paragraph) > 50:  # Skip short paragraphs
                            intro_text = paragraph
                            break
                    
                    kenya_data["introduction"] = intro_text if intro_text else fallback_data.get("introduction", "Not found")
                except Exception as e:
                    print(f"Error extracting introduction: {e}")
                    kenya_data["introduction"] = fallback_data.get("introduction", "Not found")
                
            except Exception as e:
                print(f"Error scraping Wikipedia: {e}")
                # Use fallback data for Wikipedia data
                for key in ["country", "capital", "official_languages", "population", "area", "currency", "introduction"]:
                    if key not in kenya_data and key in fallback_data:
                        kenya_data[key] = fallback_data[key]
            
            # Now scrape tourism information from Kenya Tourism Board
            try:
                print("Scraping tourism information...")
                await page.goto('https://magicalkenya.com/things-to-do/', {'timeout': 60000})
                
                # Add random delay to avoid detection
                await asyncio.sleep(random.uniform(2, 5))
                
                # Extract tourism highlights
                tourism_sections = page.locator('.elementor-widget-container h2')
                tourism_highlights = []
                
                for i in range(min(5, await tourism_sections.count())):
                    title = await tourism_sections.nth(i).inner_text()
                    if title and len(title) > 3:  # Skip empty or very short titles
                        tourism_highlights.append(title)
                
                kenya_data["tourism_highlights"] = tourism_highlights if tourism_highlights else fallback_data.get("tourism_highlights", [])
            except Exception as e:
                print(f"Error scraping tourism information: {e}")
                # Use fallback data for tourism highlights
                if "tourism_highlights" in fallback_data:
                    kenya_data["tourism_highlights"] = fallback_data["tourism_highlights"]
                else:
                    kenya_data["tourism_highlights"] = []
            
            await browser.close()
            
            # Save to JSON file
            with open('kenya_data.json', 'w', encoding='utf-8') as f:
                json.dump(kenya_data, f, ensure_ascii=False, indent=2)
                
            print("Data scraped successfully and saved to kenya_data.json")
            return kenya_data
            
    except Exception as e:
        print(f"Critical error during scraping: {e}")
        
        # If we have fallback data, use it
        if fallback_data:
            print("Using fallback data due to critical error")
            with open('kenya_data.json', 'w', encoding='utf-8') as f:
                json.dump(fallback_data, f, ensure_ascii=False, indent=2)
            return fallback_data
        
        # If no fallback data, create minimal data
        minimal_data = {
            "country": "Kenya",
            "capital": "Nairobi",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "error": "Scraping failed, minimal data provided"
        }
        
        with open('kenya_data.json', 'w', encoding='utf-8') as f:
            json.dump(minimal_data, f, ensure_ascii=False, indent=2)
        
        return minimal_data

# Run the scraper
if __name__ == "__main__":
    asyncio.run(scrape_kenya_data())
