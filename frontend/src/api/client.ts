// Backend client. Requests are relative so Vite's dev proxy forwards them to
// FastAPI; set VITE_API_BASE_URL to point at a backend on another origin.

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export type Health = {
  status: string;
  model: string;
  gateway: string;
  chat_mode: string;
  api_key_configured: boolean;
  images_mounted: boolean;
};

export type SizeStock = {
  size: string;
  quantity: number;
};

export type ProductSummary = {
  product_id: string;
  name: string;
  garment_type: string;
  short_description: string;
  colors: string[];
  price: number;
  image_url: string;
  total_stock: number;
  desirability: number;
};

export type Product = {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  colors: string[];
  search_tags: string[];
  image_file_path: string;
  image_url: string;
  price: number;
  inventory: SizeStock[];
  total_stock: number;
};

export type ChatProductCard = {
  product_id: string;
  name: string;
  price: number;
  image_url: string;
  short_description: string;
  garment_type: string;
  in_stock: boolean;
};

export type ChatResponse = {
  reply: string;
  products: ChatProductCard[];
  stub: boolean;
};

export type StoredMessage = {
  role: "user" | "assistant";
  content: string;
  products: ChatProductCard[];
};

export type ChatContext = {
  userId?: number;
  email?: string;
  currentProductId?: string;
};

export type PublicUser = {
  id: number;
  first_name: string | null;
  last_name: string | null;
  email: string;
  phone: string | null;
};

export type SignupInput = {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  password: string;
  confirm_password: string;
};

// Pull a human-readable message out of FastAPI's error shapes without ever
// surfacing echoed field values.
function errorMessage(status: number, body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
  }
  return `Request failed (${status}).`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      // non-JSON error body; fall through to the generic message
    }
    throw new Error(errorMessage(response.status, body));
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<Health> {
  return request<Health>("/api/health");
}

export function listProducts(): Promise<ProductSummary[]> {
  return request<ProductSummary[]>("/api/products");
}

export function getProduct(productId: string): Promise<Product> {
  return request<Product>(`/api/products/${encodeURIComponent(productId)}`);
}

export function getRelatedProducts(productId: string): Promise<ProductSummary[]> {
  return request<ProductSummary[]>(
    `/api/products/${encodeURIComponent(productId)}/related`,
  );
}

export function signup(input: SignupInput): Promise<PublicUser> {
  return request<PublicUser>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function login(email: string, password: string): Promise<PublicUser> {
  return request<PublicUser>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function sendChat(
  message: string,
  context: ChatContext = {},
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      user_id: context.userId,
      email: context.email,
      current_product_id: context.currentProductId,
    }),
  });
}

export function getChatHistory(
  userId: number,
  email: string,
): Promise<StoredMessage[]> {
  const params = new URLSearchParams({ user_id: String(userId), email });
  return request<StoredMessage[]>(`/api/chat/history?${params.toString()}`);
}

export type SizeChartRow = {
  size: string;
  us: string;
  uk: string;
  chest_in: string;
  chest_cm: string;
};

export type SizeRecommendation = {
  recommended_size: string;
  us: string;
  uk: string;
  chest_in: string;
  chest_cm: string;
  rationale: string;
  note: string;
};

export function getSizeGuide(): Promise<SizeChartRow[]> {
  return request<SizeChartRow[]>("/api/size-guide");
}

export function getSizeRecommendation(
  height: number,
  weight: number,
  units: "metric" | "imperial",
): Promise<SizeRecommendation> {
  return request<SizeRecommendation>("/api/size-recommendation", {
    method: "POST",
    body: JSON.stringify({ height, weight, units }),
  });
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`;
}
