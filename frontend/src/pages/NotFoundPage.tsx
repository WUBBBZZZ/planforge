import { AppShell } from "../components/AppShell";

export function NotFoundPage() {
  return (
    <AppShell currentPath="" title="Page not found">
      <section className="pf-empty-state">
        <p className="pf-muted">
          That address is not part of Planforge. Use the navigation links above or
          return to the <a href="/week">Week view</a>.
        </p>
      </section>
    </AppShell>
  );
}
