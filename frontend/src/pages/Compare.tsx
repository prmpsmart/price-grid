import { api } from '../lib/api';
import { money, num, when } from '../lib/format';
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

export default function Compare() {
  const { search, navigate } = useRouter();
  const goodId = new URLSearchParams(search).get('good') ?? '';
  const { data, loading, error } = useAsync(
    () => (goodId ? api.compare(goodId) : Promise.resolve(null)),
    [goodId],
  );

  const cheapest = data?.markets.length
    ? data.markets.reduce((a, b) =>
        num(b.current_price) < num(a.current_price) ? b : a,
      )
    : null;

  return (
    <>
      <PageHeader eyebrow="Compare" title="Where is it cheapest?">
        <GoodSelect
          value={goodId}
          onChange={(id) => navigate(id ? `/compare?good=${id}` : '/compare')}
        />
      </PageHeader>

      {!goodId ? (
        <Empty>Pick a good to compare its current price across markets.</Empty>
      ) : loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} />
      ) : !data?.markets.length ? (
        <Empty>No market has a price for {data?.good} yet.</Empty>
      ) : (
        <div className="grid gap-6 md:grid-cols-[1fr_16rem]">
          <div className="card">
            <p className="eyebrow mb-4">
              {data.good} · per {data.unit}
            </p>
            <BarChart
              bars={data.markets.map((m) => ({
                label: m.market,
                sub: m.city,
                value: num(m.current_price),
                text: money(m.current_price, m.currency),
              }))}
            />
          </div>
          {cheapest && (
            <div className="card h-fit">
              <p className="eyebrow">Best price</p>
              <p className="mt-2 font-display text-2xl text-down">
                {money(cheapest.current_price, cheapest.currency)}
              </p>
              <p className="mt-1 text-sm">
                {cheapest.market}, {cheapest.city}
              </p>
              <p className="mt-3 text-xs text-forest-muted">
                Updated {when(cheapest.submitted_at)}
              </p>
            </div>
          )}
        </div>
      )}
    </>
  );
}
