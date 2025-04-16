import { Hono } from "hono"
import { cors } from "hono/cors"
import { cache } from "hono/cache"
import { logger } from "hono/logger"
import { prettyJSON } from "hono/pretty-json"
import { 
  monitoringMiddleware, 
  healthCheckHandler, 
  metricsHandler 
} from "../middleware"

import {
  getCountry,
  getCities,
  getBorders,
  getGeography,
  getClimate,
  getEthnicGroups,
  getHistory,
  getTourism,
  getReferences,
} from "./lib/db"

// Create the Hono app
const app = new Hono()

// Add middleware
app.use("*", logger())
app.use("*", prettyJSON())
app.use("*", cors())
app.use("*", monitoringMiddleware)  // Add monitoring middleware

// Add monitoring endpoints
app.get("/health", healthCheckHandler)
app.get("/metrics", metricsHandler)

// Add cache middleware for GET requests (1 hour)
app.use(
  "/api/*",
  cache({
    cacheName: "kenya-api-cache",
    cacheControl: "max-age=3600",
  }),
)

// Root endpoint with API documentation
app.get("/", (c) => {
  return c.html(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Kenya Data API</title>
      <style>
        body {
          font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          line-height: 1.6;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          color: #333;
        }
        h1 { color: #d62828; }
        h2 { color: #003049; }
        code {
          background: #f5f5f5;
          padding: 2px 5px;
          border-radius: 4px;
        }
        pre {
          background: #f5f5f5;
          padding: 15px;
          border-radius: 8px;
          overflow-x: auto;
        }
        .endpoint {
          margin-bottom: 30px;
          border-bottom: 1px solid #eee;
          padding-bottom: 20px;
        }
      </style>
    </head>
    <body>
      <h1>Kenya Data API</h1>
      <p>This API provides comprehensive information about Kenya scraped from various sources and stored in a Neon PostgreSQL database.</p>
      
      <h2>Available Endpoints</h2>
      
      <div class="endpoint">
        <h3>GET /api/all</h3>
        <p>Returns all available data about Kenya.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/all</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/basic</h3>
        <p>Returns basic information about Kenya (country, capital, languages, etc).</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/basic</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/cities</h3>
        <p>Returns information about major cities in Kenya.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/cities</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/borders</h3>
        <p>Returns information about Kenya's neighboring countries.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/borders</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/geography</h3>
        <p>Returns information about Kenya's geographical features.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/geography</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/climate</h3>
        <p>Returns information about Kenya's climate zones.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/climate</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/ethnic-groups</h3>
        <p>Returns information about Kenya's ethnic groups.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/ethnic-groups</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/history</h3>
        <p>Returns information about Kenya's historical periods.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/history</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/tourism</h3>
        <p>Returns information about tourist attractions in Kenya.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/tourism</code></p>
      </div>
      
      <div class="endpoint">
        <h3>GET /api/references</h3>
        <p>Returns reference sources for Kenya data.</p>
        <p>Example: <code>curl https://your-worker.your-subdomain.workers.dev/api/references</code></p>
      </div>
    </body>
    </html>
  `)
})

// Helper function to get country ID
async function getKenyaId(c: any) {
  const country = await getCountry("Kenya")
  if (!country) {
    return c.json({ error: "Country data not found" }, 404)
  }
  return country.id
}

// API endpoint to get all Kenya data
app.get("/api/all", async (c) => {
  try {
    const country = await getCountry("Kenya")

    if (!country) {
      return c.json({ error: "Country data not found" }, 404)
    }

    const countryId = country.id

    const [cities, borders, geography, climate, ethnicGroups, history, tourism, references] = await Promise.all([
      getCities(countryId),
      getBorders(countryId),
      getGeography(countryId),
      getClimate(countryId),
      getEthnicGroups(countryId),
      getHistory(countryId),
      getTourism(countryId),
      getReferences(countryId),
    ])

    return c.json({
      country,
      cities,
      borders,
      geography,
      climate,
      ethnic_groups: ethnicGroups,
      history,
      tourism,
      references,
    })
  } catch (error) {
    console.error("Error fetching all data:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get basic information
app.get("/api/basic", async (c) => {
  try {
    const country = await getCountry("Kenya")

    if (!country) {
      return c.json({ error: "Country data not found" }, 404)
    }

    return c.json(country)
  } catch (error) {
    console.error("Error fetching basic data:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get cities
app.get("/api/cities", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const cities = await getCities(countryId)

    return c.json({
      cities,
      count: cities.length,
    })
  } catch (error) {
    console.error("Error fetching cities:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get borders
app.get("/api/borders", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const borders = await getBorders(countryId)

    return c.json({
      borders,
      count: borders.length,
    })
  } catch (error) {
    console.error("Error fetching borders:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get geography
app.get("/api/geography", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const geography = await getGeography(countryId)

    return c.json({
      geography,
      count: geography.length,
    })
  } catch (error) {
    console.error("Error fetching geography:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get climate
app.get("/api/climate", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const climate = await getClimate(countryId)

    return c.json({
      climate,
      count: climate.length,
    })
  } catch (error) {
    console.error("Error fetching climate:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get ethnic groups
app.get("/api/ethnic-groups", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const ethnicGroups = await getEthnicGroups(countryId)

    return c.json({
      ethnic_groups: ethnicGroups,
      count: ethnicGroups.length,
    })
  } catch (error) {
    console.error("Error fetching ethnic groups:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get history
app.get("/api/history", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const history = await getHistory(countryId)

    return c.json({
      history,
      count: history.length,
    })
  } catch (error) {
    console.error("Error fetching history:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get tourism
app.get("/api/tourism", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const tourism = await getTourism(countryId)

    return c.json({
      tourism,
      count: tourism.length,
    })
  } catch (error) {
    console.error("Error fetching tourism:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// API endpoint to get references
app.get("/api/references", async (c) => {
  try {
    const countryId = await getKenyaId(c)
    const references = await getReferences(countryId)

    return c.json({
      references,
      count: references.length,
    })
  } catch (error) {
    console.error("Error fetching references:", error)
    return c.json({ error: "Failed to fetch data" }, 500)
  }
})

// Handle 404 errors
app.notFound((c) => {
  return c.json(
    {
      status: 404,
      message: "Not found",
      available_endpoints: [
        "/api/all",
        "/api/basic",
        "/api/cities",
        "/api/borders",
        "/api/geography",
        "/api/climate",
        "/api/ethnic-groups",
        "/api/history",
        "/api/tourism",
        "/api/references",
      ],
    },
    404,
  )
})

app.onError((err, c) => {
  console.error(`Error in ${c.req.method} ${c.req.path}:`, err)
  
  return c.json({
    error: err.message || "Internal Server Error",
    status: err instanceof Error ? 500 : 400,
  }, err instanceof Error ? 500 : 400)
})

export default app
