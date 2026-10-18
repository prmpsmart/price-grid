import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './lib/api';
import type { Good, Market, Vendor } from './lib/types';
import { CatalogContext } from './catalog-context';

// Price records carry ids only, so goods/markets are loaded once and used to
// resolve names across every page.
export default function CatalogProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [goods, setGoods] = useState<Good[]>([]);
  const [markets, setMarkets] = useState<Market[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    const [g, m, v] = await Promise.all([
      api.goods(),
      api.markets(),
      api.vendors(),
    ]);
    setGoods(g.items);
    setMarkets(m.items);
    setVendors(v.items);
  }, []);

  useEffect(() => {
    reload()
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [reload]);

  const value = useMemo(() => {
    const g = new Map(goods.map((x) => [x.id, x.name]));
    const m = new Map(markets.map((x) => [x.id, x.name]));
    return {
      goods,
      markets,
      vendors,
      loading,
      reload,
      goodName: (id: string) => g.get(id) ?? 'Unknown good',
      marketName: (id: string) => m.get(id) ?? 'Unknown market',
    };
  }, [goods, markets, vendors, loading, reload]);

  return (
    <CatalogContext.Provider value={value}>{children}</CatalogContext.Provider>
  );
}
