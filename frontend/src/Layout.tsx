import { useEffect, useState } from 'react';
import { FiLogIn, FiLogOut, FiMenu, FiX } from 'react-icons/fi';
import { useAuth } from './auth-context';
import { NAV } from './nav';
import { Link } from './router';
import { useRouter } from './router-context';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { path } = useRouter();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => setMenuOpen(false), [path]);

  const items = NAV.filter((n) => !n.auth || user);

  const nav = (
    <nav className="flex flex-col">
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`flex items-center gap-3 px-5 py-4 font-display text-sm uppercase tracking-wider transition-all duration-300 ${
            path === item.href
              ? 'bg-forest-deep text-forest-warm'
              : 'text-forest-text hover:bg-forest-elevated'
          }`}
        >
          <item.icon aria-hidden /> {item.label}
        </Link>
      ))}
    </nav>
  );

  const account = user ? (
    <div className="border-t border-forest-elevated p-5">
      <p className="truncate text-sm text-forest-text">{user.email}</p>
      <p className="eyebrow mb-3 mt-1">{user.role}</p>
      <button onClick={logout} className="btn-outline w-full !py-2">
        <FiLogOut aria-hidden /> Sign out
      </button>
    </div>
  ) : (
    <div className="border-t border-forest-elevated p-5">
      <Link href="/login" className="btn-primary w-full">
        <FiLogIn aria-hidden /> Sign in
      </Link>
    </div>
  );

  return (
    <section className="relative min-h-screen w-full bg-forest-bg">
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_top_left,#69847433,transparent_60%)]" />

      {/* Desktop sidebar */}
      <aside className="fixed left-0 top-0 z-[1000] hidden h-[100dvh] w-[14rem] flex-col justify-between overflow-y-auto border-r border-[#B6C7AA30] bg-forest-sidebar/90 backdrop-blur-md md:flex">
        <div>
          <Link
            href="/"
            className="block border-b border-forest-elevated px-5 py-6 font-display text-lg font-semibold tracking-wide text-forest-warm"
          >
            <img src="/logo.svg" alt="" className="mb-3 h-12 w-12" />
            PriceGrid
            <span className="eyebrow mt-1 block !text-[10px]">
              market price intelligence
            </span>
          </Link>
          {nav}
        </div>
        {account}
      </aside>

      {/* Mobile bar */}
      <header className="fixed inset-x-0 top-0 z-[1000] flex items-center justify-between border-b border-[#B6C7AA30] bg-forest-sidebar/95 px-5 py-3 backdrop-blur-md md:hidden">
        <Link
          href="/"
          className="flex items-center gap-2 font-display text-lg font-semibold text-forest-warm"
        >
          <img src="/logo.svg" alt="" className="h-8 w-8" />
          PriceGrid
        </Link>
        <button
          aria-label="Toggle menu"
          onClick={() => setMenuOpen((o) => !o)}
          className="text-2xl text-forest-text"
        >
          {menuOpen ? <FiX /> : <FiMenu />}
        </button>
      </header>
      {menuOpen && (
        <div className="fixed inset-x-0 top-[3.25rem] z-[999] max-h-[calc(100dvh-3.25rem)] overflow-y-auto bg-forest-sidebar md:hidden">
          {nav}
          {account}
        </div>
      )}

      <main className="relative z-10 px-5 pb-16 pt-24 md:ml-[14rem] md:px-10 md:pt-12">
        <div className="mx-auto max-w-5xl">{children}</div>
      </main>
    </section>
  );
}
