import { createContext, useContext } from 'react';
import type { Role, User } from './lib/types';

export const AuthContext = createContext<{
  user: User | null;
  /** False until the stored token (if any) has been checked. */
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}>({
  user: null,
  ready: false,
  login: async () => {},
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

/** Mirrors the service-layer rules: the API is the authority, this is UX. */
export const can = (
  user: User | null,
  action: 'submit' | 'configure' | 'manage',
) => {
  const roles: Role[] = action === 'submit' ? ['vendor', 'admin'] : ['admin'];
  return !!user && roles.includes(user.role);
};
