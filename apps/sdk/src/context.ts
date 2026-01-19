/**
 * Context extraction from publisher page
 */

export interface PageContext {
  url: string;
  title: string | null;
  headings: string[];
  visible_text: string | null;
  meta_description: string | null;
}

export interface EnvironmentContext {
  device_type: 'desktop' | 'tablet' | 'mobile';
  viewport_width: number;
  viewport_height: number;
  user_agent: string;
}

/**
 * Extract page context
 */
export function extractPageContext(): PageContext {
  // Get URL
  const url = window.location.href;

  // Get title
  const title = document.title || null;

  // Get headings (H1-H3)
  const headings: string[] = [];
  const headingElements = document.querySelectorAll('h1, h2, h3');
  headingElements.forEach((el) => {
    const text = el.textContent?.trim();
    if (text) {
      headings.push(text);
    }
  });

  // Get visible text (sample from body)
  let visible_text: string | null = null;
  try {
    const bodyText = document.body.innerText || document.body.textContent;
    if (bodyText) {
      // Take first 1000 characters
      visible_text = bodyText.substring(0, 1000).trim();
    }
  } catch (e) {
    console.warn('Error extracting visible text:', e);
  }

  // Get meta description
  let meta_description: string | null = null;
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) {
    meta_description = metaDesc.getAttribute('content');
  }

  return {
    url,
    title,
    headings: headings.slice(0, 10), // Limit to 10 headings
    visible_text,
    meta_description,
  };
}

/**
 * Extract environment context
 */
export function extractEnvironmentContext(): EnvironmentContext {
  // Detect device type
  const width = window.innerWidth;
  let device_type: 'desktop' | 'tablet' | 'mobile' = 'desktop';
  
  if (width < 768) {
    device_type = 'mobile';
  } else if (width < 1024) {
    device_type = 'tablet';
  }

  return {
    device_type,
    viewport_width: window.innerWidth,
    viewport_height: window.innerHeight,
    user_agent: navigator.userAgent,
  };
}

/**
 * Get ad slot dimensions
 */
export function getAdSlotDimensions(element: HTMLElement): { width: number | null; height: number | null } {
  try {
    const rect = element.getBoundingClientRect();
    return {
      width: rect.width > 0 ? Math.round(rect.width) : null,
      height: rect.height > 0 ? Math.round(rect.height) : null,
    };
  } catch (e) {
    return { width: null, height: null };
  }
}

