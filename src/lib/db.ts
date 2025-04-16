import { neon } from "@neondatabase/serverless"
import { drizzle } from "drizzle-orm/neon-http"

// Initialize the SQL client with the database URL from environment variables
const sql = neon(process.env.DATABASE_URL!)

// Initialize the Drizzle ORM instance
export const db = drizzle(sql)

// Helper function to execute raw SQL queries
export async function executeQuery(query: string, params: any[] = []) {
  try {
    const result = await sql(query, params)
    return result
  } catch (error) {
    console.error("Database query error:", error)
    throw error
  }
}

// Helper function to get a single country by ID or name
export async function getCountry(identifier: string | number) {
  let query = ""
  let params: any[] = []

  if (typeof identifier === "number") {
    query = "SELECT * FROM country WHERE id = $1"
    params = [identifier]
  } else {
    query = "SELECT * FROM country WHERE name ILIKE $1"
    params = [`%${identifier}%`]
  }

  const result = await sql(query, params)
  return result.length > 0 ? result[0] : null
}

// Helper function to get all cities for a country
export async function getCities(countryId: number) {
  const query = "SELECT * FROM cities WHERE country_id = $1 ORDER BY is_capital DESC, population DESC NULLS LAST"
  return await sql(query, [countryId])
}

// Helper function to get all borders for a country
export async function getBorders(countryId: number) {
  const query = "SELECT * FROM borders WHERE country_id = $1"
  return await sql(query, [countryId])
}

// Helper function to get all geography features for a country
export async function getGeography(countryId: number) {
  const query = "SELECT * FROM geography WHERE country_id = $1"
  return await sql(query, [countryId])
}

// Helper function to get all climate information for a country
export async function getClimate(countryId: number) {
  const query = "SELECT * FROM climate WHERE country_id = $1"
  return await sql(query, [countryId])
}

// Helper function to get all ethnic groups for a country
export async function getEthnicGroups(countryId: number) {
  const query = "SELECT * FROM ethnic_groups WHERE country_id = $1 ORDER BY percentage DESC NULLS LAST"
  return await sql(query, [countryId])
}

// Helper function to get all historical periods for a country
export async function getHistory(countryId: number) {
  const query = "SELECT * FROM history WHERE country_id = $1 ORDER BY start_year ASC"
  return await sql(query, [countryId])
}

// Helper function to get all tourism attractions for a country
export async function getTourism(countryId: number) {
  const query = "SELECT * FROM tourism WHERE country_id = $1"
  return await sql(query, [countryId])
}

// Helper function to get all references for a country
export async function getReferences(countryId: number) {
  const query = "SELECT * FROM reference_sources WHERE country_id = $1"
  return await sql(query, [countryId])
}
