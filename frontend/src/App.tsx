import { useEffect, useState } from "react";

import { Button } from "./components/Button";
import { EmptyState } from "./components/EmptyState";
import { LoadingIndicator } from "./components/LoadingIndicator";
import { fetchHealth } from "./lib/api";
import { applyTheme, getStoredThemePreference } from "./lib/theme";
import { DevComponentsPage } from "./pages/DevComponentsPage";

type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; status: string }
  | { kind: "error"; message: string };

function StatusPage() {
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    applyTheme(getStoredThemePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((payload) => {
        if (!cancelled) {
          setHealth({ kind: "ok", status: payload.status });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Unknown backend error";
          setHealth({ kind: "error", message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="pf-app">
      <a className="pf-skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="pf-header">
        <div className="pf-header__inner">
          <p className="pf-brand">Planforge</p>
          <nav aria-label="Primary">
            <ul className="pf-nav">
              <li>
                <a href="/" aria-current="page">
                  Status
                </a>
              </li>
              <li>
                <a href="/dev/components">Components</a>
              </li>
              <li>
                <span aria-disabled="true">Today</span>
              </li>
              <li>
                <span aria-disabled="true">Week</span>
              </li>
              <li>
                <span aria-disabled="true">Month</span>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" className="pf-main">
        <section className="pf-panel" aria-labelledby="status-title">
          <h1 id="status-title">Development status</h1>
          <p>
            Planforge infrastructure is online. Product requirements are drafted in{" "}
            <code>docs/requirements/</code>. Planner features are not yet implemented.
          </p>

          <div className="pf-status-card" aria-live="polite">
            <h2>Backend health</h2>
            {health.kind === "loading" ? (
              <LoadingIndicator label="Checking backend health" />
            ) : null}
            {health.kind === "ok" ? (
              <p>
                API responded with status: <strong>{health.status}</strong>
              </p>
            ) : null}
            {health.kind === "error" ? (
              <p role="alert">Backend unavailable: {health.message}</p>
            ) : null}
          </div>

          <EmptyState
            title="Planner views are not available yet"
            description="Start with Slice 1 (one-time tasks + Today) after ADR 0006 date/time decisions are accepted."
            action={<Button disabled>Coming soon</Button>}
          />
        </section>
      </main>

      <footer className="pf-footer">
        <p>Local-first planning platform — fabricated demo data only.</p>
      </footer>
    </div>
  );
}

function App() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";

  if (path === "/dev/components") {
    return <DevComponentsPage />;
  }

  return <StatusPage />;
}

export default App;
