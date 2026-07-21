import { useEffect, useState } from "react";

import { Button } from "./components/Button";
import { EmptyState } from "./components/EmptyState";
import { LoadingIndicator } from "./components/LoadingIndicator";
import { fetchHealth } from "./lib/api";
import { applyTheme, getStoredThemePreference } from "./lib/theme";

type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; status: string }
  | { kind: "error"; message: string };

function App() {
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
                <a href="#status" aria-current="page">
                  Status
                </a>
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
        <section id="status" className="pf-panel" aria-labelledby="status-title">
          <h1 id="status-title">Development status</h1>
          <p>
            Planforge infrastructure is online. Planner features are planned and not yet
            implemented.
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
            description="Today, Week, Month, and backlog screens will appear here after product requirements and vertical feature slices are implemented."
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

export default App;
