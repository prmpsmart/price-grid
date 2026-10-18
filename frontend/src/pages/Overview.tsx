import { api } from '../lib/api';
import { useCatalog } from '../catalog-context';
import { money, num, pct, when } from '../lib/format';
import { useAsync } from '../lib/useAsync';
import { Link } from '../router';
import { Empty, ErrorBox, Loading, PageHeader, Stat } from '../components/ui';

export default function Overview() {
  const { goods, markets, vendors, goodName, marketName } = useCatalog();
  const prices = useAsync(() => api.currentPrices({}), []);
  const alerts = useAsync(() => api.alerts(), []);

  return (
    <>
      <PageHeader eyebrow="Overview" title="Market snapshot" />

      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Goods" value={goods.length} />
        <Stat label="Markets" value={markets.length} />
        <Stat label="Vendors" value={vendors.length} />
        <Stat label="Spike alerts" value={alerts.data?.total ?? '–'} />
      </div>

      <h2 className="eyebrow mb-3">Current prices</h2>
      {prices.loading ? (
        <Loading />
      ) : prices.error ? (
        <ErrorBox message={prices.error} />
      ) : !prices.data?.items.length ? (
        <Empty>No prices submitted yet.</Empty>
      ) : (
        <div className="card overflow-x-auto !p-2">
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">Good</th>
                <th className="th">Market</th>
                <th className="th text-right">Price</th>
                <th className="th hidden sm:table-cell">Updated</th>
              </tr>
            </thead>
            <tbody>
              {prices.data.items.map((p) => (
                <tr key={p.id}>
                  <td className="td">
                    <Link
                      href={`/compare?good=${p.good_id}`}
                      className="text-forest-warm hover:underline"
                    >
                      {goodName(p.good_id)}
                    </Link>
                  </td>
                  <td className="td">{marketName(p.market_id)}</td>
                  <td className="td text-right font-mono">
                    {money(p.price, p.currency)}
                  </td>
                  <td className="td hidden text-forest-muted sm:table-cell">
                    {when(p.submitted_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mb-3 mt-10 flex items-center justify-between">
        <h2 className="eyebrow">Latest spikes</h2>
        <Link
          href="/alerts"
          className="text-sm text-forest-muted hover:underline"
        >
          View all
        </Link>
      </div>
      {alerts.loading ? (
        <Loading />
      ) : alerts.error ? (
        // /alerts needs an admin token; the rest of the page stays public.
        <Empty>Sign in as an admin to see the alert feed.</Empty>
      ) : !alerts.data?.items.length ? (
        <Empty>No spikes detected. Prices are steady.</Empty>
      ) : (
        <ul className="space-y-3">
          {alerts.data.items.slice(0, 4).map((a) => (
            <li
              key={a.id}
              className="card flex flex-wrap justify-between gap-2"
            >
              <span>
                <strong className="text-forest-warm">
                  {goodName(a.good_id)}
                </strong>{' '}
                in {marketName(a.market_id)}
              </span>
              <span className="font-mono text-sm text-up">
                {num(a.delta_pct) > 0 ? '+' : ''}
                {pct(a.delta_pct)} · {money(a.price, a.currency)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
