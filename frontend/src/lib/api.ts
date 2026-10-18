import type {
  CompareResponse,
  Good,
  Market,
  Paginated,
  PriceAlert,
  PriceRecord,
  TrendResponse,
  User,
  Vendor,
} from './types';

const BASE = `${import.meta.env.VITE_API_BASE ?? ''}/api/v1`;
const TOKEN_KEY = 'pricegrid.token';

export const tokenStore = {
  get: () => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set: (token: string | null) => {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* storage unavailable: session lasts until reload */
    }
  },
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

type Query = Record<string, string | number | undefined | null>;

async function request<T>(
  method: string,
  path: string,
  opts: { query?: Query; body?: unknown } = {},
): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  for (const [k, v] of Object.entries(opts.query ?? {}))
    if (v !== undefined && v !== null && v !== '')
      url.searchParams.set(k, String(v));

  const headers: Record<string, string> = {};
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.body) headers['Content-Type'] = 'application/json';

  const res = await fetch(url, {
    method,
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    // FastAPI sends a string for HTTPException and a list for validation.
    const msg = Array.isArray(d)
      ? d.map((e: { msg: string }) => e.msg).join(', ')
      : (d ?? res.statusText);
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

const get = <T>(path: string, query?: Query) =>
  request<T>('GET', path, { query });
const post = <T>(path: string, body: unknown) =>
  request<T>('POST', path, { body });

export const api = {
  login: (email: string, password: string) =>
    post<{ access_token: string }>('/auth/login', { email, password }),
  register: (email: string, password: string, role: string) =>
    post<User>('/auth/register', { email, password, role }),
  me: () => get<User>('/auth/me'),

  goods: () => get<Paginated<Good>>('/goods', { limit: 100 }),
  createGood: (b: Pick<Good, 'name' | 'category' | 'unit' | 'description'>) =>
    post<Good>('/goods', b),
  markets: () => get<Paginated<Market>>('/markets', { limit: 100 }),
  createMarket: (b: Pick<Market, 'name' | 'city' | 'region'>) =>
    post<Market>('/markets', b),
  vendors: () => get<Paginated<Vendor>>('/vendors', { limit: 100 }),
  createVendor: (b: { name: string; location?: string }) =>
    post<Vendor>('/vendors', b),

  currentPrices: (q: { good_id?: string; market_id?: string; page?: number }) =>
    get<Paginated<PriceRecord>>('/prices/current', { limit: 100, ...q }),
  history: (goodId: string, page = 1) =>
    get<Paginated<PriceRecord>>(`/prices/history/${goodId}`, {
      page,
      limit: 100,
    }),
  compare: (goodId: string) =>
    get<CompareResponse>('/prices/compare', { good_id: goodId }),
  trends: (goodId: string, window: string) =>
    get<TrendResponse>('/prices/trends', { good_id: goodId, window }),
  submitPrice: (b: {
    good_id: string;
    vendor_id: string;
    market_id: string;
    price: number;
    currency: string;
  }) => post<PriceRecord>('/prices', b),

  alerts: (page = 1) =>
    get<Paginated<PriceAlert>>('/alerts', { page, limit: 20 }),
  alertsByGood: (goodId: string) =>
    get<Paginated<PriceAlert>>(`/alerts/${goodId}`, { limit: 20 }),
  setThreshold: (b: {
    good_id: string;
    market_id: string;
    threshold_pct: number;
  }) => post<void>('/alerts/thresholds', b),
};
