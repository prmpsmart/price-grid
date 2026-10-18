import { useMemo, useState } from 'react';
import { api } from '../lib/api';
import { useCatalog } from '../catalog-context';
import { money, num, when } from '../lib/format';
import { useAsync } from '../lib/useAsync';
import { useRouter } from '../router-context';
import LineChart from '../components/LineChart';
import {
  Empty,
  ErrorBox,
  GoodSelect,
  Loading,
  PageHeader,
} from '../components/ui';

export default function History() {
  const { search, navigate } = useRouter();
  const { marketName } = useCatalog();
  const goodId = new URLSearchParams(search).get('good') ?? '';
  const [marketId, setMarketId] = useState('');
  const { data, loading, error } = useAsync(
    () => (goodId ? api.history(goodId) : Promise.resolve(null)),
    [goodId],
  );

  const markets = useMemo(
    () => [...new Set(data?.items.map((p) => p.market_id))],
    [data],
  );
  const rows = useMemo(
    () =>
      (data?.items ?? []).filter((p) => !marketId || p.market_id === marketId),
    [data, marketId],
  );
  const points = useMemo(
    () =>
      [...rows]
        .sort((a, b) => a.submitted_at.localeCompare(b.submitted_at))
        .map((p) => ({ t: p.submitted_at, v: num(p.price) })),
    [rows],
  );

  return (
    <>
      <PageHeader eyebrow="History" title="Price over time">
        <div className="flex flex-wrap gap-3">
          <GoodSelect
            value={goodId}
            onChange={(id) => {
              setMarketId('');
              navigate(id ? `/history?good=${id}` : '/history');
            }}
          />
          {markets.length > 1 && (
            <select
              className="field max-w-xs"
              value={marketId}
              onChange={(e) => setMarketId(e.target.value)}
            >
              <option value="">All markets</option>
              {markets.map((id) => (
                <option key={id} value={id}>
                  {marketName(id)}
                </option>
              ))}
            </select>
          )}
        </div>
      </PageHeader>

      {!goodId ? (
        <Empty>Pick a good to see every price ever submitted for it.</Empty>
      ) : loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} />
      ) : !rows.length ? (
        <Empty>No price records yet.</Empty>
      ) : (
        <>
          <div className="card mb-6">
            {/* Mixing markets in one line is misleading; ask for one. */}
            {marketId || markets.length === 1 ? (
              <LineChart points={points} />
            ) : (
              <p className="py-6 text-center text-sm text-forest-muted">
                Choose a market to plot its price line.
              </p>
            )}
          </div>
          <div className="card overflow-x-auto !p-2">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="th">Market</th>
                  <th className="th text-right">Price</th>
                  <th className="th">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => (
                  <tr key={p.id}>
                    <td className="td">{marketName(p.market_id)}</td>
                    <td className="td text-right font-mono">
                      {money(p.price, p.currency)}
                    </td>
                    <td className="td text-forest-muted">
                      {when(p.submitted_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
