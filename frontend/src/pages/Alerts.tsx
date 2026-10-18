import { FormEvent, useState } from 'react';
import { api } from '../lib/api';
import { can, useAuth } from '../auth-context';
import { useCatalog } from '../catalog-context';
import { money, num, pct, when } from '../lib/format';
import { useAsync } from '../lib/useAsync';
import { Empty, ErrorBox, Loading, PageHeader } from '../components/ui';

function ThresholdForm() {
  const { goods, markets } = useCatalog();
  const [goodId, setGoodId] = useState('');
  const [marketId, setMarketId] = useState('');
  const [threshold, setThreshold] = useState('20');
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.setThreshold({
        good_id: goodId,
        market_id: marketId,
        threshold_pct: Number(threshold),
      });
      setMsg({ ok: true, text: 'Threshold saved.' });
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message });
    }
  };

  return (
    <form onSubmit={submit} className="card mb-8 grid gap-4 md:grid-cols-4">
      <div>
        <label className="label">Good</label>
        <select
          required
          className="field"
          value={goodId}
          onChange={(e) => setGoodId(e.target.value)}
        >
          <option value="">Select…</option>
          {goods.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="label">Market</label>
        <select
          required
          className="field"
          value={marketId}
          onChange={(e) => setMarketId(e.target.value)}
        >
          <option value="">Select…</option>
          {markets.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="label">Spike threshold %</label>
        <input
          required
          type="number"
          min="0"
          step="0.1"
          className="field"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
        />
      </div>
      <div className="flex items-end">
        <button className="btn-primary w-full">Set threshold</button>
      </div>
      {msg && (
        <p
          className={`text-sm md:col-span-4 ${msg.ok ? 'text-down' : 'text-up'}`}
        >
          {msg.text}
        </p>
      )}
    </form>
  );
}

export default function Alerts() {
  const { user } = useAuth();
  const { goodName, marketName } = useCatalog();
  const [page, setPage] = useState(1);
  const { data, loading, error } = useAsync(
    () => (user ? api.alerts(page) : Promise.resolve(null)),
    [user, page],
  );

  return (
    <>
      <PageHeader eyebrow="Alerts" title="Price spikes" />
      {can(user, 'configure') && <ThresholdForm />}

      {!user ? (
        <Empty>Sign in as an admin to view the spike feed.</Empty>
      ) : loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} />
      ) : !data?.items.length ? (
        <Empty>No spikes detected. Prices are steady.</Empty>
      ) : (
        <>
          <ul className="space-y-3">
            {data.items.map((a) => (
              <li
                key={a.id}
                className="card grid gap-2 md:grid-cols-[1fr_auto] md:items-center"
              >
                <div>
                  <p className="text-forest-warm">
                    {goodName(a.good_id)}{' '}
                    <span className="text-forest-text">
                      in {marketName(a.market_id)}
                    </span>
                  </p>
                  <p className="text-xs text-forest-muted">
                    {when(a.triggered_at)} · avg was{' '}
                    {money(a.previous_avg, a.currency)} · limit{' '}
                    {pct(a.threshold_pct)}
                  </p>
                </div>
                <p className="font-mono text-lg text-up">
                  {num(a.delta_pct) > 0 ? '+' : ''}
                  {pct(a.delta_pct)}
                  <span className="ml-3 text-forest-warm">
                    {money(a.price, a.currency)}
                  </span>
                </p>
              </li>
            ))}
          </ul>
          <div className="mt-6 flex items-center justify-center gap-4">
            <button
              className="btn-outline !py-2"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span className="eyebrow">
              Page {data.page} · {data.total} total
            </span>
            <button
              className="btn-outline !py-2"
              disabled={page * data.limit >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </>
  );
}
