/**
 * Persona data extraction from external website
 * Reads persona data from URL parameters or session storage
 */

export interface PersonaData {
  time_of_day?: 'day' | 'night';
  location?: 'east' | 'west' | 'central' | 'unknown';
  weather?: 'sunny' | 'rainy' | 'snowy';
  temperature?: string;
  os?: 'apple' | 'windows' | 'android' | 'other';
  device_type?: 'mobile' | 'tablet' | 'desktop';
}

/**
 * Extract persona data from URL parameters
 * 
 * URL examples:
 * - ?time_of_day=day&location=east&weather=snowy&temperature=-10 C&os=apple&device_type=desktop
 */
function extractPersonaFromURL(): PersonaData | null {
  const urlParams = new URLSearchParams(window.location.search);
  
  const timeOfDay = urlParams.get('time_of_day');
  const location = urlParams.get('location');
  const weather = urlParams.get('weather');
  const temperature = urlParams.get('temperature');
  const os = urlParams.get('os');
  const deviceType = urlParams.get('device_type');
  
  if (timeOfDay || location || weather || temperature || os || deviceType) {
    const data: PersonaData = {};
    if (timeOfDay) data.time_of_day = timeOfDay as 'day' | 'night';
    if (location) data.location = location as 'east' | 'west' | 'central' | 'unknown';
    if (weather) data.weather = weather as 'sunny' | 'rainy' | 'snowy';
    if (temperature) data.temperature = temperature;
    if (os) data.os = os as 'apple' | 'windows' | 'android' | 'other';
    if (deviceType) data.device_type = deviceType as 'mobile' | 'tablet' | 'desktop';
    return Object.keys(data).length > 0 ? data : null;
  }
  
  return null;
}

/**
 * Extract persona data from session storage
 * External website can set: sessionStorage.setItem('ai_ads_persona', JSON.stringify({...}))
 */
function extractPersonaFromStorage(): PersonaData | null {
  try {
    const stored = sessionStorage.getItem('ai_ads_persona');
    if (stored) {
      return JSON.parse(stored) as PersonaData;
    }
  } catch (e) {
    console.warn('[Persona] Error reading from sessionStorage:', e);
  }
  return null;
}

/**
 * Store persona data in session storage for persistence across pages
 */
function storePersonaInStorage(persona: PersonaData): void {
  try {
    sessionStorage.setItem('ai_ads_persona', JSON.stringify(persona));
  } catch (e) {
    console.warn('[Persona] Error storing in sessionStorage:', e);
  }
}

/**
 * Extract persona data from external website
 * Priority: URL parameters > Session storage
 * 
 * Behavior:
 * - If URL has persona params → use them and store in sessionStorage
 * - If URL has no query params → clear sessionStorage (explicit removal of params)
 * - SessionStorage is only used when explicitly set by external website, not as fallback
 * 
 * @returns Persona data or null if not found
 */
export function extractPersonaData(): PersonaData | null {
  // Try URL parameters first (highest priority)
  const urlPersona = extractPersonaFromURL();
  if (urlPersona) {
    // Store in session storage for persistence across pages
    storePersonaInStorage(urlPersona);
    console.log('[Persona] Using persona from URL params:', urlPersona);
    return urlPersona;
  }
  
  // If URL has no persona params, clear sessionStorage
  // This ensures that removing params from URL clears the persona data
  try {
    const hadStorage = sessionStorage.getItem('ai_ads_persona') !== null;
    sessionStorage.removeItem('ai_ads_persona');
    if (hadStorage) {
      console.log('[Persona] Cleared sessionStorage (no persona params in URL)');
    }
  } catch (e) {
    console.warn('[Persona] Error clearing sessionStorage:', e);
  }
  
  // Don't use sessionStorage as fallback - only use it if explicitly set by external website
  // This prevents stale persona data from being used when params are removed
  console.log('[Persona] No persona data found (URL has no persona params)');
  return null;
}
