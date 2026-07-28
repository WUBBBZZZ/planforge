import type { ReactNode } from "react";

export interface AppShellProps {
  currentPath: string;
  title: string;
  children: ReactNode;
  actions?: ReactNode;
}

function navCurrent(path: string, currentPath: string): "page" | undefined {
  if (path === "/" && (currentPath === "/" || currentPath === "/week")) {
    return "page";
  }
  return currentPath === path ? "page" : undefined;
}

export function AppShell({
  currentPath,
  title,
  children,
  actions,
}: AppShellProps) {
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
                <a href="/week" aria-current={navCurrent("/week", currentPath)}>
                  Week
                </a>
              </li>
              <li>
                <a href="/month" aria-current={navCurrent("/month", currentPath)}>
                  Month
                </a>
              </li>
              <li>
                <a href="/today" aria-current={navCurrent("/today", currentPath)}>
                  Today
                </a>
              </li>
              <li>
                <a href="/backlog" aria-current={navCurrent("/backlog", currentPath)}>
                  Backlog
                </a>
              </li>
              <li>
                <a href="/routines" aria-current={navCurrent("/routines", currentPath)}>
                  Routines
                </a>
              </li>
              <li>
                <a href="/settings" aria-current={navCurrent("/settings", currentPath)}>
                  Settings
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" className="pf-main">
        <div className="pf-page-header">
          <h1>{title}</h1>
          {actions ? <div className="pf-page-header__actions">{actions}</div> : null}
        </div>
        {children}
      </main>

      <footer className="pf-footer">
        <div className="pf-footer__inner">
          <p>Local-first planning platform — fabricated demo data only.</p>
        </div>
      </footer>
    </div>
  );
}
