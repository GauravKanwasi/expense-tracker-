import { useState } from "react";

export default function AuthScreen({
  mode,
  form,
  error,
  loading,
  onModeChange,
  onChange,
  onSubmit
}) {
  const isRegister = mode === "register";
  const [showPassword, setShowPassword] = useState(false);

  return (
    <main className="auth-page">
      <section className="auth-showcase">
        <div className="auth-motion-background" aria-hidden="true" />
        <div className="showcase-brand">
          <span className="brand-mark">L</span>
          <strong>Ledgerly</strong>
        </div>
        <div className="showcase-copy">
          <p className="eyebrow">A CLEARER MONEY ROUTINE</p>
          <h1>Give every rupee a place to go.</h1>
          <p>
            A calm workspace for the small decisions that make your bigger
            financial picture easier to understand.
          </p>
        </div>
        <div className="showcase-metrics">
          <div><strong>01</strong><span>Track every entry</span></div>
          <div><strong>02</strong><span>Plan each month</span></div>
          <div><strong>03</strong><span>See the pattern</span></div>
        </div>
        <div className="showcase-orbit orbit-one" />
        <div className="showcase-orbit orbit-two" />
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <p className="eyebrow">{isRegister ? "GET STARTED" : "WELCOME BACK"}</p>
          <h2>{isRegister ? "Create your workspace" : "Sign in to Ledgerly"}</h2>
          <p className="auth-subtitle">
            {isRegister
              ? "Start with a simple, private view of your money."
              : "Your financial overview is waiting for you."}
          </p>

          {error && <div className="alert alert-error" role="alert">{error}</div>}

          <form className="auth-form" onSubmit={onSubmit}>
            {isRegister && (
              <label>
                Your name
                <input
                  name="name"
                  type="text"
                  placeholder="Sapna"
                  value={form.name}
                  onChange={onChange}
                  minLength="1"
                  maxLength="100"
                  required
                />
              </label>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={onChange}
                required
              />
            </label>
            <label className="password-field">
              Password
              <span className="password-input">
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="At least 8 characters"
                  value={form.password}
                  onChange={onChange}
                  minLength="8"
                  maxLength="128"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((visible) => !visible)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </span>
            </label>
            <button className="button button-primary button-full" disabled={loading}>
              {loading ? "Please wait..." : isRegister ? "Create account" : "Sign in"}
            </button>
          </form>

          <p className="auth-switch">
            {isRegister ? "Already have an account?" : "New to Ledgerly?"}
            <button onClick={() => onModeChange(isRegister ? "login" : "register")}>
              {isRegister ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>
      </section>
    </main>
  );
}
