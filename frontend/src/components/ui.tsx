import { ReactNode } from 'react';
import { useCatalog } from '../catalog-context';

export function PageHeader({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="font-display text-3xl font-semibold text-forest-text">
          {title}
        </h1>
      </div>
      {children}
    </header>
  );
}

export function Loading() {
  return <p className="eyebrow animate-pulse py-10 text-center">Loading…</p>;
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-up/40 bg-up/10 px-4 py-3 text-sm text-up">
      {message}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="card py-12 text-center text-sm text-forest-muted">
      {children}
    </div>
  );
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="card">
      <p className="eyebrow">{label}</p>
      <p className="mt-2 font-display text-3xl font-semibold text-forest-warm">
        {value}
      </p>
    </div>
  );
}

export function GoodSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (id: string) => void;
}) {
  const { goods } = useCatalog();
  return (
    <select
      className="field max-w-xs"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">Select a good…</option>
      {goods.map((g) => (
        <option key={g.id} value={g.id}>
          {g.name} ({g.unit})
        </option>
      ))}
    </select>
  );
}
