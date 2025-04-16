import asyncio
import os
import re
import json
import time
import traceback
from datetime import datetime
from playwright.async_api import async_playwright
import psycopg2
from psycopg2.extras import execute_values
import requests
from logger import  setup_logger  

# Set up logger
logger = setup_logger("kenya_scraper", "logs/kenya_scraper.log")

# Database connection string from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Monitoring configuration
MONITORING_WEBHOOK_URL = os.environ.get("MONITORING_WEBHOOK_URL")  # For Slack, Discord, etc.
HEALTHCHECK_URL = os.environ.get("HEALTHCHECK_URL")  # For services like healthchecks.io

# Metrics
scraper_metrics = {
    "start_time": None,
    "end_time": None,
    "duration_seconds": 0,
    "pages_scraped": 0,
    "items_extracted": 0,
    "errors": 0,
    "database_operations": 0,
    "status": "not_started"  # not_started, running, completed, failed
}

def update_metric(key, value):
    """Update a metric and log it"""
    scraper_metrics[key] = value
    logger.info(f"Metric updated: {key}={value}")

def send_monitoring_alert(message, is_error=False):
    """Send an alert to the configured webhook"""
    if not MONITORING_WEBHOOK_URL:
        logger.warning("No monitoring webhook URL configured, skipping alert")
        return
    
    try:
        level = "ERROR" if is_error else "INFO"
        payload = {
            "text": f"[{level}] Kenya Scraper: {message}",
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(MONITORING_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            logger.warning(f"Failed to send alert: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Error sending alert: {e}")

def ping_healthcheck(status="success"):
    """Ping a health check service to indicate the scraper's status"""
    if not HEALTHCHECK_URL:
        logger.warning("No healthcheck URL configured, skipping ping")
        return
    
    try:
        url = f"{HEALTHCHECK_URL}/{'fail' if status == 'fail' else ''}"
        response = requests.get(url)
        logger.info(f"Healthcheck ping ({status}): {response.status_code}")
    except Exception as e:
        logger.error(f"Error pinging healthcheck: {e}")

async def scrape_kenya_data():
    """Main scraper function with monitoring"""
    update_metric("start_time", datetime.now().isoformat())
    update_metric("status", "running")
    send_monitoring_alert("Scraper started")
    
    try:
        # Existing scraper code from before, with added metrics and logging
        logger.info("Starting Kenya data scraper...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Set a realistic user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Dictionary to store all scraped data
            kenya_data = {
                "country": {},
                "cities": [],
                "borders": [],
                "geography": [],
                "climate": [],
                "ethnic_groups": [],
                "history": [],
                "tourism": [],
                "references": []
            }
            
            # Scrape general information about Kenya from Wikipedia
            logger.info("Scraping Wikipedia for general information...")
            try:
                await page.goto('https://en.wikipedia.org/wiki/Kenya', {'timeout': 60000})
                update_metric("pages_scraped", scraper_metrics["pages_scraped"] + 1)
                
                # Add random delay to avoid detection
                await asyncio.sleep(2)
                
                # Extract basic country information
                country_name = await page.locator('h1#firstHeading').inner_text()
                logger.info(f"Extracted country name: {country_name}")
                update_metric("items_extracted", scraper_metrics["items_extracted"] + 1)
                
                # ... [rest of the scraping code, with added logging and metrics] ...
                # For brevity, I'm not including all the scraping code here, but you would
                # add logging statements and update metrics throughout the original code
                
                # Example for one section:
                logger.info("Extracting cities information...")
                cities_section = page.locator('h2:has-text("Largest cities"), h3:has-text("Largest cities")')
                if await cities_section.count() > 0:
                    # Try to find a table with cities
                    cities_table = page.locator('h2:has-text("Largest cities") + div table, h3:has-text("Largest cities") + div table')
                    if await cities_table.count() > 0:
                        rows = cities_table.locator('tbody tr')
                        for i in range(1, min(11, await rows.count())):  # Skip header row, get top 10
                            row = rows.nth(i)
                            cells = row.locator('td')
                            if await cells.count() >= 2:
                                city_name = await cells.nth(0).inner_text()
                                city_pop = await cells.nth(1).inner_text()
                                city_pop = re.sub(r'[^\d]', '', city_pop)
                                
                                kenya_data["cities"].append({
                                    "name": city_name.strip(),
                                    "population": city_pop if city_pop else None,
                                    "population_year": 2019,
                                    "is_capital": city_name.strip() == "Nairobi"
                                })
                                update_metric("items_extracted", scraper_metrics["items_extracted"] + 1)
                                logger.info(f"Extracted city: {city_name}")
                
                # Continue with the rest of the scraping code...
            
            except Exception as e:
                logger.error(f"Error scraping Wikipedia: {e}")
                update_metric("errors", scraper_metrics["errors"] + 1)
                # Use fallback data as in the original code
            
            # Continue with the rest of the scraping functions...
            
            await browser.close()
            
            # Save to JSON file as backup
            with open('kenya_data_full.json', 'w', encoding='utf-8') as f:
                json.dump(kenya_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Data scraped successfully and saved to kenya_data_full.json")
            
            # Store in database
            try:
                store_in_database(kenya_data)
                update_metric("database_operations", scraper_metrics["database_operations"] + 1)
            except Exception as e:
                logger.error(f"Database error: {e}")
                update_metric("errors", scraper_metrics["errors"] + 1)
                send_monitoring_alert(f"Database error: {str(e)}", is_error=True)
            
            update_metric("status", "completed")
            update_metric("end_time", datetime.now().isoformat())
            start_time = datetime.fromisoformat(scraper_metrics["start_time"])
            end_time = datetime.fromisoformat(scraper_metrics["end_time"])
            duration = (end_time - start_time).total_seconds()
            update_metric("duration_seconds", duration)
            
            # Send completion alert with metrics
            send_monitoring_alert(
                f"Scraper completed in {duration:.2f}s. "
                f"Pages: {scraper_metrics['pages_scraped']}, "
                f"Items: {scraper_metrics['items_extracted']}, "
                f"Errors: {scraper_metrics['errors']}"
            )
            
            # Ping healthcheck
            ping_healthcheck("success")
            
            return kenya_data
    
    except Exception as e:
        logger.error(f"Critical error during scraping: {e}")
        logger.error(traceback.format_exc())
        update_metric("status", "failed")
        update_metric("errors", scraper_metrics["errors"] + 1)
        update_metric("end_time", datetime.now().isoformat())
        
        # Calculate duration
        start_time = datetime.fromisoformat(scraper_metrics["start_time"])
        end_time = datetime.fromisoformat(scraper_metrics["end_time"])
        duration = (end_time - start_time).total_seconds()
        update_metric("duration_seconds", duration)
        
        # Send failure alert
        send_monitoring_alert(
            f"Scraper failed after {duration:.2f}s: {str(e)}\n{traceback.format_exc()}", 
            is_error=True
        )
        
        # Ping healthcheck with failure
        ping_healthcheck("fail")
        
        # If we have fallback data, use it
        if os.path.exists('kenya_data_full.json'):
            try:
                with open('kenya_data_full.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Minimal data as a last resort
        return {
            "country": {
                "name": "Kenya",
                "capital": "Nairobi",
                "error": "Scraping failed, minimal data provided"
            }
        }

def store_in_database(data):
    """Store the scraped data in the Neon PostgreSQL database"""
    logger.info("Storing data in Neon PostgreSQL database...")
    
    conn = None
    cursor = None
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Insert country data
        country = data["country"]
        cursor.execute("""
            INSERT INTO country (
                name, official_name, capital, largest_city, area_total, area_unit,
                population, population_year, currency, motto, anthem, official_languages, introduction
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                official_name = EXCLUDED.official_name,
                capital = EXCLUDED.capital,
                largest_city = EXCLUDED.largest_city,
                area_total = EXCLUDED.area_total,
                area_unit = EXCLUDED.area_unit,
                population = EXCLUDED.population,
                population_year = EXCLUDED.population_year,
                currency = EXCLUDED.currency,
                motto = EXCLUDED.motto,
                anthem = EXCLUDED.anthem,
                official_languages = EXCLUDED.official_languages,
                introduction = EXCLUDED.introduction,
                last_updated = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            country["name"],
            country["official_name"],
            country["capital"],
            country["largest_city"],
            country["area_total"],
            country["area_unit"],
            country["population"],
            country["population_year"],
            country["currency"],
            country["motto"],
            country["anthem"],
            country["official_languages"],
            country["introduction"]
        ))
        
        country_id = cursor.fetchone()[0]
        logger.info(f"Inserted/updated country with ID: {country_id}")
        
        # Clear existing data for this country
        tables = ["cities", "borders", "geography", "climate", "ethnic_groups", "history", "tourism", "reference_sources"]
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE country_id = %s", (country_id,))
            logger.info(f"Cleared existing data from {table}")
        
        # Insert cities data
        if data["cities"]:
            cities_data = [(
                country_id,
                city["name"],
                "City",
                city.get("population"),
                city.get("population_year"),
                f"Major city in Kenya: {city['name']}",
                city.get("is_capital", False),
                None  # coordinates
            ) for city in data["cities"]]
            
            execute_values(cursor, """
                INSERT INTO cities (
                    country_id, name, type, population, population_year, description, is_capital, coordinates
                ) VALUES %s
            """, cities_data)
            logger.info(f"Inserted {len(cities_data)} cities")
        
        # Continue with the rest of the database operations...
        # [For brevity, I'm not including all the database operations here]
        
        # Commit the transaction
        conn.commit()
        logger.info("Database transaction committed successfully")
        
    except Exception as e:
        logger.error(f"Error storing data in database: {e}")
        logger.error(traceback.format_exc())
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Save metrics to a JSON file for later analysis
def save_metrics():
    with open('logs/scraper_metrics.json', 'w') as f:
        json.dump(scraper_metrics, f, indent=2)

# Run the scraper
if __name__ == "__main__":
    try:
        asyncio.run(scrape_kenya_data())
        save_metrics()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        logger.critical(traceback.format_exc())
        save_metrics()
        # Ensure the process exits with an error code
        exit(1)