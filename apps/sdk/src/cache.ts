/**
 * Cache management for ad responses
 * Uses sessionStorage to cache generated product image URLs per page URL
 */

import { ContextResponse } from './request';
import { EnvironmentContext } from './context';

const CACHE_PREFIX = 'aiads_cache_';
const CACHE_VERSION = '1.0';

interface CacheEntry {
  url: string;
  persona_data?: EnvironmentContext['persona_data'];
  response: ContextResponse;
  cached_at: number;
}

/**
 * Generate cache key from URL and persona data
 * Same URL with different persona should have different cache entries
 */
function generateCacheKey(url: string, personaData?: EnvironmentContext['persona_data']): string {
  const baseKey = url;
  
  // Include persona data in cache key if present
  if (personaData && Object.keys(personaData).length > 0) {
    const personaStr = JSON.stringify(personaData);
    return `${baseKey}::${personaStr}`;
  }
  
  return baseKey;
}

/**
 * Get cache key for storage
 */
function getStorageKey(cacheKey: string): string {
  return `${CACHE_PREFIX}${CACHE_VERSION}_${btoa(cacheKey).replace(/[/+=]/g, '_')}`;
}

/**
 * Get cached ad response for a URL
 */
export function getCachedAds(
  url: string,
  personaData?: EnvironmentContext['persona_data']
): ContextResponse | null {
  try {
    const cacheKey = generateCacheKey(url, personaData);
    const storageKey = getStorageKey(cacheKey);
    const cached = sessionStorage.getItem(storageKey);
    
    if (!cached) {
      return null;
    }
    
    const entry: CacheEntry = JSON.parse(cached);
    
    // Verify URL matches (safety check)
    if (entry.url !== url) {
      return null;
    }
    
    console.log(`[Cache] ✅ Found cached ads for URL: ${url}`);
    return entry.response;
  } catch (error) {
    console.warn('[Cache] Error reading from cache:', error);
    return null;
  }
}

/**
 * Store ad response in cache
 */
export function setCachedAds(
  url: string,
  response: ContextResponse,
  personaData?: EnvironmentContext['persona_data']
): void {
  try {
    const cacheKey = generateCacheKey(url, personaData);
    const storageKey = getStorageKey(cacheKey);
    
    const entry: CacheEntry = {
      url,
      persona_data: personaData,
      response,
      cached_at: Date.now(),
    };
    
    sessionStorage.setItem(storageKey, JSON.stringify(entry));
    console.log(`[Cache] 💾 Cached ads for URL: ${url}`);
  } catch (error) {
    console.warn('[Cache] Error writing to cache:', error);
    // If storage is full, try to clear old entries
    if (error instanceof DOMException && error.name === 'QuotaExceededError') {
      console.warn('[Cache] Storage quota exceeded, clearing old entries...');
      clearOldCacheEntries();
    }
  }
}

/**
 * Clear cache for a specific URL
 */
export function clearCacheForUrl(url: string): void {
  try {
    // Clear all cache entries that start with this URL
    const keysToRemove: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(CACHE_PREFIX)) {
        try {
          const cached = sessionStorage.getItem(key);
          if (cached) {
            const entry: CacheEntry = JSON.parse(cached);
            if (entry.url === url) {
              keysToRemove.push(key);
            }
          }
        } catch (e) {
          // Skip invalid entries
        }
      }
    }
    
    keysToRemove.forEach(key => sessionStorage.removeItem(key));
    console.log(`[Cache] 🗑️ Cleared ${keysToRemove.length} cache entry/entries for URL: ${url}`);
  } catch (error) {
    console.warn('[Cache] Error clearing cache:', error);
  }
}

/**
 * Clear all cached ads
 */
export function clearAllCache(): void {
  try {
    const keysToRemove: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(CACHE_PREFIX)) {
        keysToRemove.push(key);
      }
    }
    
    keysToRemove.forEach(key => sessionStorage.removeItem(key));
    console.log(`[Cache] 🗑️ Cleared all cache (${keysToRemove.length} entries)`);
  } catch (error) {
    console.warn('[Cache] Error clearing all cache:', error);
  }
}

/**
 * Clear old cache entries (older than 24 hours)
 */
function clearOldCacheEntries(): void {
  try {
    const now = Date.now();
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours
    const keysToRemove: string[] = [];
    
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(CACHE_PREFIX)) {
        try {
          const cached = sessionStorage.getItem(key);
          if (cached) {
            const entry: CacheEntry = JSON.parse(cached);
            if (now - entry.cached_at > maxAge) {
              keysToRemove.push(key);
            }
          }
        } catch (e) {
          // Skip invalid entries
          keysToRemove.push(key);
        }
      }
    }
    
    keysToRemove.forEach(key => sessionStorage.removeItem(key));
    if (keysToRemove.length > 0) {
      console.log(`[Cache] 🗑️ Cleared ${keysToRemove.length} old cache entries`);
    }
  } catch (error) {
    console.warn('[Cache] Error clearing old cache entries:', error);
  }
}

/**
 * Get cache statistics
 */
export function getCacheStats(): { count: number; urls: string[] } {
  try {
    const urls = new Set<string>();
    let count = 0;
    
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(CACHE_PREFIX)) {
        try {
          const cached = sessionStorage.getItem(key);
          if (cached) {
            const entry: CacheEntry = JSON.parse(cached);
            urls.add(entry.url);
            count++;
          }
        } catch (e) {
          // Skip invalid entries
        }
      }
    }
    
    return {
      count,
      urls: Array.from(urls),
    };
  } catch (error) {
    console.warn('[Cache] Error getting cache stats:', error);
    return { count: 0, urls: [] };
  }
}
