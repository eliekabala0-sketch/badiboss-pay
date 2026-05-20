import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiClient } from "../api/client";
import { saveToken } from "../auth";

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@badibosspay.com");
  const [password, setPassword] = useState("admin12345");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const loginResponse = await apiClient.post<{ access_token: string }>("/auth/login", { email, password });
      saveToken(loginResponse.data.access_token);
      navigate("/", { replace: true });
    } catch {
      setError("Echec de connexion. Verifiez vos identifiants admin.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto mt-20 max-w-md rounded bg-white p-6 shadow">
      <h2 className="mb-4 text-xl font-semibold">Connexion Admin</h2>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <input
          className="w-full rounded border border-slate-300 px-3 py-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <input
          className="w-full rounded border border-slate-300 px-3 py-2"
          type="password"
          placeholder="Mot de passe"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          className="w-full rounded bg-blue-600 px-3 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          disabled={loading}
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </div>
  );
}

export default LoginPage;
