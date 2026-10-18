export const num = (v: string | number) => Number(v);

export const money = (v: string | number, currency: string) => {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(num(v));
  } catch {
    // Not an ISO currency code the runtime knows.
    return `${currency} ${num(v).toLocaleString()}`;
  }
};

export const pct = (v: string | number) => `${num(v).toFixed(1)}%`;

export const when = (iso: string) =>
  new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
