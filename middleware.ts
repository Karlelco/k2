import { Context, Next } from 'hono'
import { HTTPException } from 'hono/http-exception'

// Simple in-memory metrics store
// In production, you might want to use a proper metrics service
export const metrics = {
  requestCount: 0,
  errorCount: 0,
  endpointStats: {} as Record<string, {
    count: number,
    errors: number,
    totalResponseTime: number,
    avgResponseTime: number
  }>,
  startTime: Date.now(),
  lastError: null as null | {
    path: string,
    method: string,
    status: number,
    message: string,
    timestamp: string
  }
}

// Reset metrics function (useful for tests or periodic resets)
export const resetMetrics = () => {
  metrics.requestCount = 0
  metrics.errorCount = 0
  metrics.endpointStats = {}
  metrics.startTime = Date.now()
  metrics.lastError = null
}

// Monitoring middleware
export const monitoringMiddleware = async (c: Context, next: Next) => {
  const path = c.req.path
  const method = c.req.method
  const startTime = Date.now()
  
  // Initialize endpoint stats if not exists
  if (!metrics.endpointStats[path]) {
    metrics.endpointStats[path] = {
      count: 0,
      errors: 0,
      totalResponseTime: 0,
      avgResponseTime: 0
    }
  }
  
  try {
    // Increment request count
    metrics.requestCount++
    metrics.endpointStats[path].count++
    
    // Process the request
    await next()
    
    // Calculate response time
    const responseTime = Date.now() - startTime
    
    // Update response time metrics
    metrics.endpointStats[path].totalResponseTime += responseTime
    metrics.endpointStats[path].avgResponseTime = 
      metrics.endpointStats[path].totalResponseTime / metrics.endpointStats[path].count
    
    return c.res
  } catch (error) {
    // Handle errors
    metrics.errorCount++
    metrics.endpointStats[path].errors++
    
    // Record error details
    const status = error instanceof HTTPException ? error.status : 500
    const message = error instanceof Error ? error.message : 'Unknown error'
    
    metrics.lastError = {
      path,
      method,
      status,
      message,
      timestamp: new Date().toISOString()
    }
    
    // Log the error
    console.error(`[ERROR] ${method} ${path} - ${status}: ${message}`)
    
    // Rethrow to let error handlers deal with it
    throw error
  }
}

// Health check endpoint handler
export const healthCheckHandler = (c: Context) => {
  const uptime = Math.floor((Date.now() - metrics.startTime) / 1000)
  
  return c.json({
    status: 'ok',
    uptime: uptime,
    version: '1.0.0',
    timestamp: new Date().toISOString()
  })
}

// Metrics endpoint handler
export const metricsHandler = (c: Context) => {
  return c.json({
    requestCount: metrics.requestCount,
    errorCount: metrics.errorCount,
    uptime: Math.floor((Date.now() - metrics.startTime) / 1000),
    endpointStats: metrics.endpointStats,
    lastError: metrics.lastError
  })
}