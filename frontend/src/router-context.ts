import { createContext, useContext } from 'react';

export const RouterContext = createContext<{
  path: string;
  /** Query string without the leading '?'. */
  search: string;
  navigate: (to: string) => void;
}>({ path: '/', search: '', navigate: () => {} });

export const useRouter = () => useContext(RouterContext);
