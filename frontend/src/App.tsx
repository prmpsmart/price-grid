import { useEffect } from 'react';
import Layout from './Layout';
import { NAV } from './nav';
import { Link } from './router';
import { useRouter } from './router-context';
import Overview from './pages/Overview';
import Compare from './pages/Compare';
import Trends from './pages/Trends';
import History from './pages/History';
import Alerts from './pages/Alerts';
import Submit from './pages/Submit';
import Catalog from './pages/Catalog';
import Login from './pages/Login';

const PAGES: Record<string, () => JSX.Element> = {
  '/': Overview,
  '/compare': Compare,
  '/trends': Trends,
  '/history': History,
  '/alerts': Alerts,
  '/submit': Submit,
  '/catalog': Catalog,
  '/login': Login,
};

function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <p className="eyebrow">404</p>
      <h1 className="font-display text-4xl font-semibold text-forest-text">
        Page not found
      </h1>
      <Link href="/" className="btn-primary">
        Back to overview
      </Link>
    </div>
  );
}

export default function App() {
  const { path } = useRouter();
  const Page = PAGES[path] ?? NotFound;
  const label = NAV.find((n) => n.href === path)?.label;
  useEffect(() => {
    document.title = label ? `${label} · PriceGrid` : 'PriceGrid';
  }, [label]);
  return (
    <Layout>
      <Page />
    </Layout>
  );
}
