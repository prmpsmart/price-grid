import { createContext, useContext } from 'react';
import type { Good, Market, Vendor } from './lib/types';

export const CatalogContext = createContext<{
  goods: Good[];
  markets: Market[];
  vendors: Vendor[];
  loading: boolean;
  reload: () => Promise<void>;
  goodName: (id: string) => string;
  marketName: (id: string) => string;
}>({
  goods: [],
  markets: [],
  vendors: [],
  loading: true,
  reload: async () => {},
  goodName: (id) => id,
  marketName: (id) => id,
});

export const useCatalog = () => useContext(CatalogContext);
