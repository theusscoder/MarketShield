
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  Eye,
  EyeOff,
  ChartNoAxesCombined,
  Radar,
} from "lucide-react";
import { signup, login, logout,getCurrentUser } from "./services/auth";
import "./App.css";

const features = [
  {
    icon: ChartNoAxesCombined,
    title: "Simulated Trading",
    description: "Explore market dynamics without risking real money.",
  },
  {
    icon: Radar,
    title: "Detect Market Abuse",
    description: "Discover suspicious activity in simulated markets.",
  },
  {
    icon: ShieldCheck,
    title: "Learn & Explore",
    description: "Understand how fair and transparent markets work.",
  },
];

function BrandPanel({ isLogin }) {
  return (
    <section className="brand-panel">
      <div className="brand">
        <span className="brand-icon"><Activity size={23} /></span>
        <span>Market<span className="brand-accent">Shield</span></span>
      </div>

      <div className="brand-content">
        <span className="eyebrow">
          <span className="status-dot" />
          SIMULATION ENVIRONMENT
        </span>

        <h1>
          {isLogin
            ? "Trade. Monitor. Make a difference."
            : "Build fairer markets with MarketShield."}
        </h1>

        <p className="brand-description">
          Explore simulated financial markets, understand trading behavior,
          and uncover suspicious activity in a safe environment.
        </p>

        <div className="feature-list">
          {features.map(({ icon: Icon, title, description }) => (
            <div className="feature" key={title}>
              <div className="feature-icon"><Icon size={20} /></div>
              <div>
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="market-card">
          <span className="muted-label">MARKET ACTIVITY</span>
          <h3>Market integrity starts here</h3>
          <svg viewBox="0 0 440 90" className="market-chart"
            role="img" aria-label="Illustrative market activity chart">
            <path
              d="M0 68 L35 57 L70 63 L105 39 L140 48 L175 30 L210 43 L245 20 L280 34 L315 13 L350 28 L385 8 L440 16"
              fill="none"
              stroke="#35d6b0"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="chart-note">Illustrative data · Not a real market feed</p>
        </div>
      </div>

      <footer className="brand-footer">
        <span>BUILT FOR TRANSPARENCY</span>
        <span>EDUCATION · SIMULATION · INTEGRITY</span>
      </footer>
    </section>
  );
}

function Field({
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
}) {
  const [visible, setVisible] = useState(false);
  const actualType = type === "password" && visible ? "text" : type;

  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <span className="input-wrap">
        <input
          type={actualType}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required
          minLength={type === "password" ? 8 : undefined}
        />
        {type === "password" && (
          <button
            type="button"
            className="visibility-button"
            aria-label={visible ? "Hide password" : "Show password"}
            onClick={() => setVisible((current) => !current)}
          >
            {visible ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </span>
    </label>
  );
}

function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState("signup");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isLogin = mode === "login";

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
  }

  
  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!isLogin && password !== confirmPassword) {
      setError("Your passwords do not match.");
      return;
    }

    if (!isLogin && !acceptedTerms) {
      setError("Please accept the terms to create your account.");
      return;
    }

    setLoading(true);

    try {
      const result = isLogin
        ? await login({ email: email.trim(), password })
        : await signup({
            name: name.trim(),
            email: email.trim(),
            password,
          });

      if (result.requiresEmailConfirmation) {
        setError(result.message);
        return;
      }

      onAuthenticated(result.user);
    } catch (err) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }


  return (
    <main className="auth-layout">
      <BrandPanel isLogin={isLogin} />

      <section className="auth-panel">
        <div className="mobile-brand brand">
          <span className="brand-icon"><Activity size={22} /></span>
          <span>Market<span className="brand-accent">Shield</span></span>
        </div>

        <div className="auth-card">
          <div className="auth-heading">
            <span className="eyebrow">YOUR MARKET JOURNEY STARTS HERE</span>
            <h2>{isLogin ? "Welcome back." : "Create your account."}</h2>
            <p>
              {isLogin
                ? "Sign in to continue exploring MarketShield."
                : "Join the simulation and discovery the story behind the market."}
            </p>
          </div>

          <div className="auth-switch">
            <button
              type="button"
              className={!isLogin ? "active" : ""}
              onClick={() => switchMode("signup")}
            >
              Create account
            </button>
            <button
              type="button"
              className={isLogin ? "active" : ""}
              onClick={() => switchMode("login")}
            >
              Sign in
            </button>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            {!isLogin && (
              <Field
                label="Full name"
                value={name}
                onChange={setName}
                placeholder="Enter your full name"
                autoComplete="name"
              />
            )}

            <Field
              label="Email address"
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="you@example.com"
              autoComplete="email"
            />

            <Field
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
              placeholder="At least 8 characters"
              autoComplete={isLogin ? "current-password" : "new-password"}
            />

            {!isLogin && (
              <>
                <Field
                  label="Confirm password"
                  type="password"
                  value={confirmPassword}
                  onChange={setConfirmPassword}
                  placeholder="Re-enter your password"
                  autoComplete="new-password"
                />

                <label className="terms-row">
                  <input
                    type="checkbox"
                    checked={acceptedTerms}
                    onChange={(event) => setAcceptedTerms(event.target.checked)}
                  />
                  <span>
                    I agree to the terms of use and understand MarketShield
                    is a simulation platform.
                  </span>
                </label>
              </>
            )}

            {error && <p className="form-message error">{error}</p>}

            <button
              type="submit"
              className="primary-button"
              disabled={loading}
            >
              {loading
                ? "Please wait..."
                : isLogin
                  ? "Sign in to MarketShield"
                  : "Create my account"}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>

          <div className="security-note">
            <ShieldCheck size={17} />
            <span>Simulation only. No real-money trading.</span>
          </div>

          <p className="auth-bottom">
            {isLogin ? "New to MarketShield?" : "Already have an account?"}{" "}
            <button
              type="button"
              className="text-button"
              onClick={() => switchMode(isLogin ? "signup" : "login")}
            >
              {isLogin ? "Create an account" : "Sign in"}
            </button>
          </p>
        </div>

        <footer className="auth-footer">
          <span>© 2026 MarketShield</span>
          <span>Designed for fairer markets.</span>
        </footer>
      </section>
    </main>
  );
}

function Dashboard({ user, onLogout }) {
  const [role, setRole] = useState("trader");

  async function handleLogout() {
    try {
      await logout();
    } finally {
      onLogout();
    }
  }

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div className="brand">
          <span className="brand-icon"><Activity size={22} /></span>
          <span>Market<span className="brand-accent">Shield</span></span>
        </div>
        <button className="secondary-button" onClick={handleLogout}>
          Sign out
        </button>
      </header>

      <section className="dashboard-content">
        <span className="eyebrow">
          <span className="status-dot" /> DEMO ENVIRONMENT
        </span>
        <h1>Welcome, {user.name}.</h1>
        <p className="dashboard-description">
          Choose how you want to explore the MarketShield simulation.
        </p>

        <div className="role-grid">
          <button
            className={`role-card ${role === "trader" ? "selected" : ""}`}
            onClick={() => setRole("trader")}
          >
            <ChartNoAxesCombined size={28} />
            <h2>Trader</h2>
            <p>Explore the order book and practice simulated trading.</p>
            <span>{role === "trader" ? "Selected" : "Choose role"}</span>
          </button>

          <button
            className={`role-card ${role === "observer" ? "selected" : ""}`}
            onClick={() => setRole("observer")}
          >
            <Radar size={28} />
            <h2>Market Observer</h2>
            <p>Explore simulated activity and surveillance alerts.</p>
            <span>{role === "observer" ? "Selected" : "Choose role"}</span>
          </button>
        </div>

        <p className="dashboard-description">
          Selected view: {role === "trader" ? "Trader" : "Market Observer"}.
          Live market data will appear after platform integration.
        </p>
      </section>
    </main>
  );
}


export default function App() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    let active = true;

    getCurrentUser()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setCheckingSession(false);
      });

    return () => {
      active = false;
    };
  }, []);

  if (checkingSession) {
    return <main className="auth-panel">Loading MarketShield...</main>;
  }

  return user ? (
    <Dashboard user={user} onLogout={() => setUser(null)} />
  ) : (
    <AuthPage onAuthenticated={setUser} />
  );
}

