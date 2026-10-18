import type { IconType } from 'react-icons';
import {
  FiAlertTriangle,
  FiBarChart2,
  FiClock,
  FiGrid,
  FiPlusCircle,
  FiTrendingUp,
  FiDatabase,
} from 'react-icons/fi';

export const NAV: {
  href: string;
  label: string;
  icon: IconType;
  /** Only shown when signed in. */
  auth?: boolean;
}[] = [
  { href: '/', label: 'Overview', icon: FiGrid },
  { href: '/compare', label: 'Compare', icon: FiBarChart2 },
  { href: '/trends', label: 'Trends', icon: FiTrendingUp },
  { href: '/history', label: 'History', icon: FiClock },
  { href: '/alerts', label: 'Spike alerts', icon: FiAlertTriangle },
  { href: '/submit', label: 'Submit price', icon: FiPlusCircle, auth: true },
  { href: '/catalog', label: 'Catalog', icon: FiDatabase },
];
