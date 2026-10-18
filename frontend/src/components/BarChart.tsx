// Horizontal bars, one per market. Hand-rolled SVG keeps the bundle small.
export type Bar = { label: string; sub?: string; value: number; text: string };

export default function BarChart({ bars }: { bars: Bar[] }) {
  const max = Math.max(...bars.map((b) => b.value), 1);
  const min = Math.min(...bars.map((b) => b.value));
  return (
    <ul className="space-y-3">
      {bars.map((b) => (
        <li key={b.label + (b.sub ?? '')}>
          <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
            <span className="text-forest-text">
              {b.label}
              {b.sub && <span className="ml-2 text-forest-deep">{b.sub}</span>}
            </span>
            <span
              className={`font-mono ${
                b.value === min && bars.length > 1
                  ? 'text-down'
                  : 'text-forest-warm'
              }`}
            >
              {b.text}
            </span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-forest-sidebar">
            <div
              className="h-full rounded-full bg-forest-muted transition-all duration-700"
              style={{ width: `${(b.value / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
