import { FormEvent, useState } from 'react';
import { api } from '../lib/api';
import { can, useAuth } from '../auth-context';
import { useCatalog } from '../catalog-context';
import { Empty, PageHeader } from '../components/ui';

export default function Submit() {
  const { user } = useAuth();
  const { goods, markets, vendors, reload } = useCatalog();
  const [f, setF] = useState({
    good_id: '',
    market_id: '',
    vendor_id: '',
    price: '',
    currency: 'NGN',
  });
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [vendorName, setVendorName] = useState('');

  if (!can(user, 'submit'))
    return (
      <>
        <PageHeader eyebrow="Submit" title="Submit a price" />
        <Empty>Only vendors and admins can submit prices.</Empty>
      </>
    );

  // Vendors may only post as themselves; admins can pick any vendor.
  const own = vendors.find((v) => v.user_id === user?.id);
  const vendorId = user?.role === 'vendor' ? (own?.id ?? '') : f.vendor_id;
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) =>
    setF({ ...f, [k]: e.target.value });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const rec = await api.submitPrice({
        good_id: f.good_id,
        market_id: f.market_id,
        vendor_id: vendorId,
        price: Number(f.price),
        currency: f.currency.toUpperCase(),
      });
      setMsg({ ok: true, text: `Recorded ${rec.price} ${rec.currency}.` });
      setF({ ...f, price: '' });
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message });
    }
  };

  const createVendor = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.createVendor({ name: vendorName });
      await reload();
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message });
    }
  };

  if (user?.role === 'vendor' && !own)
    return (
      <>
        <PageHeader eyebrow="Submit" title="Create your vendor profile" />
        <form onSubmit={createVendor} className="card max-w-md space-y-4">
          <p className="text-sm text-forest-muted">
            You need a vendor profile before you can post prices.
          </p>
          <input
            required
            className="field"
            placeholder="Business name"
            value={vendorName}
            onChange={(e) => setVendorName(e.target.value)}
          />
          <button className="btn-primary">Create profile</button>
          {msg && <p className="text-sm text-up">{msg.text}</p>}
        </form>
      </>
    );

  return (
    <>
      <PageHeader eyebrow="Submit" title="Submit a price" />
      <form
        onSubmit={submit}
        className="card grid max-w-2xl gap-4 md:grid-cols-2"
      >
        <div>
          <label className="label">Good</label>
          <select
            required
            className="field"
            value={f.good_id}
            onChange={set('good_id')}
          >
            <option value="">Select…</option>
            {goods.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name} ({g.unit})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Market</label>
          <select
            required
            className="field"
            value={f.market_id}
            onChange={set('market_id')}
          >
            <option value="">Select…</option>
            {markets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}, {m.city}
              </option>
            ))}
          </select>
        </div>
        {user?.role === 'admin' && (
          <div className="md:col-span-2">
            <label className="label">Vendor</label>
            <select
              required
              className="field"
              value={f.vendor_id}
              onChange={set('vendor_id')}
            >
              <option value="">Select…</option>
              {vendors.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div>
          <label className="label">Price</label>
          <input
            required
            type="number"
            min="0"
            step="0.01"
            className="field"
            value={f.price}
            onChange={set('price')}
          />
        </div>
        <div>
          <label className="label">Currency (ISO)</label>
          <input
            required
            maxLength={3}
            className="field uppercase"
            value={f.currency}
            onChange={set('currency')}
          />
        </div>
        <button className="btn-primary md:col-span-2">Submit price</button>
        {msg && (
          <p
            className={`text-sm md:col-span-2 ${msg.ok ? 'text-down' : 'text-up'}`}
          >
            {msg.text}
          </p>
        )}
      </form>
    </>
  );
}
