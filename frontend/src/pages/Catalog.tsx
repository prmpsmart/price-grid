import { FormEvent, useState } from 'react';
import { api } from '../lib/api';
import { can, useAuth } from '../auth-context';
import { useCatalog } from '../catalog-context';
import { Link } from '../router';
import { PageHeader } from '../components/ui';

type Tab = 'goods' | 'markets' | 'vendors';

function AddForm({
  fields,
  onSubmit,
}: {
  fields: { key: string; label: string; required?: boolean }[];
  onSubmit: (v: Record<string, string>) => Promise<void>;
}) {
  const [v, setV] = useState<Record<string, string>>({});
  const [err, setErr] = useState('');
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await onSubmit(v);
      setV({});
      setErr('');
    } catch (x) {
      setErr((x as Error).message);
    }
  };
  return (
    <form onSubmit={submit} className="card mb-6 grid gap-3 md:grid-cols-4">
      {fields.map((f) => (
        <input
          key={f.key}
          required={f.required ?? true}
          className="field"
          placeholder={f.label}
          value={v[f.key] ?? ''}
          onChange={(e) => setV({ ...v, [f.key]: e.target.value })}
        />
      ))}
      <button className="btn-primary">Add</button>
      {err && <p className="text-sm text-up md:col-span-4">{err}</p>}
    </form>
  );
}

export default function Catalog() {
  const { user } = useAuth();
  const { goods, markets, vendors, reload } = useCatalog();
  const [tab, setTab] = useState<Tab>('goods');
  const admin = can(user, 'manage');

  return (
    <>
      <PageHeader eyebrow="Catalog" title="Goods, markets & vendors" />

      <div className="mb-6 flex gap-2">
        {(['goods', 'markets', 'vendors'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-full px-5 py-2 font-mono text-xs uppercase tracking-widest ${
              t === tab
                ? 'bg-forest-muted text-black'
                : 'border border-forest-muted/40 text-forest-text hover:bg-forest-elevated'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {admin && tab === 'goods' && (
        <AddForm
          fields={[
            { key: 'name', label: 'Name' },
            { key: 'category', label: 'Category' },
            { key: 'unit', label: 'Unit (kg, bag…)' },
            { key: 'description', label: 'Description', required: false },
          ]}
          onSubmit={async (v) => {
            await api.createGood({
              name: v.name,
              category: v.category,
              unit: v.unit,
              description: v.description || null,
            });
            await reload();
          }}
        />
      )}
      {admin && tab === 'markets' && (
        <AddForm
          fields={[
            { key: 'name', label: 'Name' },
            { key: 'city', label: 'City' },
            { key: 'region', label: 'Region' },
          ]}
          onSubmit={async (v) => {
            await api.createMarket({
              name: v.name,
              city: v.city,
              region: v.region,
            });
            await reload();
          }}
        />
      )}

      <div className="card overflow-x-auto !p-2">
        <table className="w-full">
          <thead>
            <tr>
              {tab === 'goods' && (
                <>
                  <th className="th">Name</th>
                  <th className="th">Category</th>
                  <th className="th">Unit</th>
                </>
              )}
              {tab === 'markets' && (
                <>
                  <th className="th">Name</th>
                  <th className="th">City</th>
                  <th className="th">Region</th>
                </>
              )}
              {tab === 'vendors' && (
                <>
                  <th className="th">Name</th>
                  <th className="th">Location</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {tab === 'goods' &&
              goods.map((g) => (
                <tr key={g.id}>
                  <td className="td">
                    <Link
                      href={`/compare?good=${g.id}`}
                      className="text-forest-warm hover:underline"
                    >
                      {g.name}
                    </Link>
                  </td>
                  <td className="td">{g.category}</td>
                  <td className="td">{g.unit}</td>
                </tr>
              ))}
            {tab === 'markets' &&
              markets.map((m) => (
                <tr key={m.id}>
                  <td className="td text-forest-warm">{m.name}</td>
                  <td className="td">{m.city}</td>
                  <td className="td">{m.region}</td>
                </tr>
              ))}
            {tab === 'vendors' &&
              vendors.map((v) => (
                <tr key={v.id}>
                  <td className="td text-forest-warm">{v.name}</td>
                  <td className="td">{v.location ?? '–'}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
