import { AnchorHTMLAttributes, MouseEvent, useEffect, useState } from 'react';
import { RouterContext, useRouter } from './router-context';

// A tiny pushState router. The host must serve index.html for unknown paths
// (Vite's dev server does; see README for production).

const normalize = (p: string) => (p.length > 1 ? p.replace(/\/+$/, '') : p);

export function Router({ children }: { children: React.ReactNode }) {
  const [path, setPath] = useState(normalize(window.location.pathname));
  const [search, setSearch] = useState(window.location.search.slice(1));

  useEffect(() => {
    const onPop = () => {
      setPath(normalize(window.location.pathname));
      setSearch(window.location.search.slice(1));
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const navigate = (to: string) => {
    const url = new URL(to, window.location.origin);
    window.history.pushState({}, '', url.pathname + url.search);
    setPath(normalize(url.pathname));
    setSearch(url.search.slice(1));
    window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
  };

  return (
    <RouterContext.Provider value={{ path, search, navigate }}>
      {children}
    </RouterContext.Provider>
  );
}

export function Link({
  href,
  onClick,
  ...rest
}: AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) {
  const { navigate } = useRouter();
  const handle = (e: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(e);
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button)
      return;
    e.preventDefault();
    navigate(href);
  };
  return <a href={href} onClick={handle} {...rest} />;
}
