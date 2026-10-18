import { FormEvent, useState } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../auth-context';
import { useRouter } from '../router-context';
import { PageHeader } from '../components/ui';

export default function Login() {
  const { login } = useAuth();
  const { navigate } = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('viewer');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === 'register') await api.register(email, password, role);
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="Account"
        title={mode === 'login' ? 'Sign in' : 'Create account'}
      />
      <form onSubmit={submit} className="card max-w-md space-y-4">
        <div>
          <label className="label">Email</label>
          <input
            required
            type="email"
            className="field"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="label">Password</label>
          <input
            required
            type="password"
            className="field"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {mode === 'register' && (
          <div>
            <label className="label">Role</label>
            <select
              className="field"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="viewer">Viewer — read-only</option>
              <option value="vendor">Vendor — can submit prices</option>
              <option value="admin">Admin — full access</option>
            </select>
          </div>
        )}
        {error && <p className="text-sm text-up">{error}</p>}
        <button disabled={busy} className="btn-primary w-full">
          {mode === 'login' ? 'Sign in' : 'Register'}
        </button>
        <button
          type="button"
          className="w-full text-center text-sm text-forest-muted hover:underline"
          onClick={() => {
            setMode(mode === 'login' ? 'register' : 'login');
            setError('');
          }}
        >
          {mode === 'login'
            ? 'No account? Register'
            : 'Already registered? Sign in'}
        </button>
      </form>
    </>
  );
}
