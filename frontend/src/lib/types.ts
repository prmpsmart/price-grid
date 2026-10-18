export type Role = 'admin' | 'vendor' | 'viewer';

type Base = { id: string; created_at: string; updated_at: string };

export type User = Base & { email: string; role: Role };
export type Good = Base & {
  name: string;
  category: string;
  unit: string;
  description: string | null;
};
export type Market = Base & { name: string; city: string; region: string };
export type Vendor = Base & {
  name: string;
  location: string | null;
  user_id: string;
};
export type PriceRecord = Base & {
  good_id: string;
  vendor_id: string;
  market_id: string;
  // Decimals are serialised as strings or numbers depending on the field.
  price: string | number;
  currency: string;
  submitted_at: string;
};
export type PriceAlert = Base & {
  good_id: string;
  market_id: string;
  price: string | number;
  previous_avg: string | number;
  delta_pct: string | number;
  threshold_pct: string | number;
  currency: string;
  triggered_at: string;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  limit: number;
};

export type CompareResponse = {
  good_id: string;
  good: string;
  unit: string;
  markets: {
    market_id: string;
    market: string;
    city: string;
    current_price: string | number;
    currency: string;
    submitted_at: string;
  }[];
};

export type TrendResponse = {
  good_id: string;
  good: string;
  unit: string;
  window: string;
  markets: {
    market_id: string;
    market: string;
    city: string;
    avg_price: string | number;
    currency: string;
    data_points: number;
  }[];
};
