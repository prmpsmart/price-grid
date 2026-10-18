import { useState } from 'react';
import { api } from '../lib/api';
import { money, num } from '../lib/format';
import { useAsync } from '../lib/useAsync';
import { useRouter } from '../router-context';
import BarChart from '../components/BarChart';
import {
  Empty,
  ErrorBox,
  GoodSelect,
  Loading,
  PageHeader,
} from '../components/ui';

const WINDOWS = ['7d', '30d', '90d'];

export default function Trends() {
  const { search, navigate } = useRouter();
  const goodId = new URLSearchParams(search).get('good') ?? '';
  const [window, setWindow] = useState('30d');
  const { data, loading, error } = useAsync(
    () => (goodId ? api.trends(goodId, window) : Promise.resolve(null)),
    [goodId, window],
  );

  return (
    <>
      <PageHeader eyebrow="Trends" title="Average price by market">
        <div className="flex flex-wrap items-center gap-3">
          <GoodSelect
            value={goodId}
            onChange={(id) => navigate(id ? `/trends?good=${id}` : '/trends')}
          />
          <div className="flex overflow-hidden rounded-full border border-forest-muted/40">
            {WINDOWS.map((w) => (
              <button
                key={w}
                onClick={() => setWindow(w)}
                className={`px-4 py-2 font-mono text-xs ${
                  w === window
                    ? 'bg-forest-muted text-black'
                    : 'text-forest-text hover:bg-forest-elevated'
                }`}
              >
                {w}
              </button>
            ))}
          </div>
        </div>
      </PageHeader>

      {!goodId ? (
        <Empty>Pick a good to see its rolling average per market.</Empty>
      ) : loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} />
      ) : !data?.markets.length ? (
        <Empty>
          No data points for {data?.good} in the last {window}.
        </Empty>
      ) : (
        <div className="card">
          <p className="eyebrow mb-4">
            {data.good} · {data.window} average per {data.unit}
          </p>
          <BarChart
            bars={data.markets.map((m) => ({
              label: m.market,
              sub: `${m.city} · ${m.data_points} pts`,
              value: num(m.avg_price),
              text: money(m.avg_price, m.currency),
            }))}
          />
        </div>
      )}
    </>
  );
}
