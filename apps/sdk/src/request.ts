/**
 * Ad request to backend
 */

import { PageContext, EnvironmentContext } from './context';

export interface AdRequestPayload {
  publisher_id: string;
  url: string;
  device_type: string;
  viewport_width: number;
  viewport_height: number;
  user_agent: string;
  slot_id: string;
  slot_width: number | null;
  slot_height: number | null;
}

export interface MatchedProduct {
  id: string;
  name: string;
  description: string;
  price: number | null;
  currency: string;
  image_url: string;
  edited_image_url?: string;  // AI-edited image matching page styling
  landing_url: string;
  match_score: number;
}

export interface ContextResponse {
  success: boolean;
  context: {
    url: string;
    title: string | null;
    headings: string[];
    keywords: string[];
    topics: string[];
    has_enriched: boolean;
  };
  matched_products: MatchedProduct[];
  timestamp: string;
}

/**
 * Request context and matched products from backend
 */
export async function requestContext(
  apiEndpoint: string,
  publisherId: string,
  pageContext: PageContext,
  envContext: EnvironmentContext,
  slotId: string,
  slotDimensions: { width: number | null; height: number | null }
): Promise<ContextResponse> {
  const payload: AdRequestPayload = {
    publisher_id: publisherId,
    url: pageContext.url,
    device_type: envContext.device_type,
    viewport_width: envContext.viewport_width,
    viewport_height: envContext.viewport_height,
    user_agent: envContext.user_agent,
    slot_id: slotId,
    slot_width: slotDimensions.width,
    slot_height: slotDimensions.height,
  };

  try {
    const response = await fetch(`${apiEndpoint}/extract_context`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: ContextResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Error requesting context:', error);
    throw error;
  }
}

