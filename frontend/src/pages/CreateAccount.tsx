import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signup } from "../api/client";
import { useAuth } from "../auth/context";

export default function CreateAccount() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    // Catch the mismatch in the browser too, for a faster, clearer message.
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      const user = await signup({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        phone: form.phone.trim() || undefined,
        password: form.password,
        confirm_password: form.confirm_password,
      });
      setUser(user);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page page-narrow">
      <section className="hero hero-compact">
        <p className="eyebrow">Join us</p>
        <h1>Create an account</h1>
      </section>

      <form className="form" onSubmit={onSubmit}>
        {error && <p className="notice error form-error">{error}</p>}
        <div className="form-row">
          <label>
            First name
            <input
              type="text"
              autoComplete="given-name"
              value={form.first_name}
              onChange={update("first_name")}
              required
            />
          </label>
          <label>
            Last name
            <input
              type="text"
              autoComplete="family-name"
              value={form.last_name}
              onChange={update("last_name")}
              required
            />
          </label>
        </div>
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            placeholder="you@yale.edu"
            value={form.email}
            onChange={update("email")}
            required
          />
        </label>
        <label>
          Phone <span className="optional">(optional, for shipping)</span>
          <input
            type="tel"
            autoComplete="tel"
            placeholder="203-555-0100"
            value={form.phone}
            onChange={update("phone")}
          />
        </label>
        <label>
          Password <span className="optional">(at least 8 characters)</span>
          <input
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={update("password")}
            minLength={8}
            required
          />
        </label>
        <label>
          Confirm password
          <input
            type="password"
            autoComplete="new-password"
            value={form.confirm_password}
            onChange={update("confirm_password")}
            required
          />
        </label>
        <button type="submit" className="btn btn-solid btn-block" disabled={busy}>
          {busy ? "Creating…" : "Create account"}
        </button>
        <p className="form-note">
          Already have one?{" "}
          <Link to="/login" className="text-link">
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}
