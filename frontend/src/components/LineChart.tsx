import { when } from '../lib/format';

export type Point = { t: string; v: number };

const W = 640;
const H = 220;
const P = { l: 48, r: 12, t: 12, b: 24 };

export default function LineChart({ points }: { points: Point[] }) {
  if (points.length < 2)
    return (
      <p className="py-10 text-center text-sm text-forest-muted">
        Not enough data points to draw a line yet.
      </p>
    );

  const times = points.map((p) => new Date(p.t).getTime());
  const [t0, t1] = [Math.min(...times), Math.max(...times)];
  const lo = Math.min(...points.map((p) => p.v));
  const hi = Math.max(...points.map((p) => p.v));
  const pad = (hi - lo || hi || 1) * 0.1;
  const [y0, y1] = [lo - pad, hi + pad];

  const x = (t: number) => P.l + ((t - t0) / (t1 - t0 || 1)) * (W - P.l - P.r);
  const y = (v: number) => H - P.b - ((v - y0) / (y1 - y0)) * (H - P.t - P.b);

  const path = points
    .map((p, i) => `${i ? 'L' : 'M'}${x(new Date(p.t).getTime())},${y(p.v)}`)
    .join(' ');
  const ticks = [y0 + pad, (y0 + y1) / 2, y1 - pad];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img">
      {ticks.map((v) => (
        <g key={v}>
          <line
            x1={P.l}
            x2={W - P.r}
            y1={y(v)}
            y2={y(v)}
            stroke="#B6C7AA"
            strokeOpacity={0.15}
          />
          <text
            x={P.l - 8}
            y={y(v) + 4}
            textAnchor="end"
            className="fill-forest-muted font-mono text-[10px]"
          >
            {v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </text>
        </g>
      ))}
      <path d={path} fill="none" stroke="#B6C7AA" strokeWidth={2} />
      {points.map((p) => (
        <circle
          key={p.t}
          cx={x(new Date(p.t).getTime())}
          cy={y(p.v)}
          r={3}
          fill="#F6E6CB"
        >
          <title>{`${p.v.toLocaleString()} · ${when(p.t)}`}</title>
        </circle>
      ))}
    </svg>
  );
}
