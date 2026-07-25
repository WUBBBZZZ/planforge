import { useState } from "react";

import {
  Badge,
  Button,
  Card,
  Checkbox,
  Dialog,
  EmptyState,
  FormField,
  Input,
  LoadingIndicator,
  Select,
  Textarea,
} from "../components";

export function DevComponentsPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [exampleChecked, setExampleChecked] = useState(true);

  return (
    <div className="pf-app">
      <a className="pf-skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="pf-header">
        <div className="pf-header__inner">
          <p className="pf-brand">Planforge — component gallery</p>
          <nav aria-label="Primary">
            <ul className="pf-nav">
              <li>
                <a href="/week">Week</a>
              </li>
              <li>
                <a href="/today">Today</a>
              </li>
              <li>
                <a href="/dev/components" aria-current="page">
                  Components
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" className="pf-main pf-gallery">
        <h1>UI primitives (fabricated examples only)</h1>
        <p className="pf-muted">
          Development gallery for shared components. Not a planner screen.
        </p>

        <div className="pf-gallery__grid">
          <Card title="Buttons">
            <div className="pf-gallery__row">
              <Button>Primary action</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="ghost">Ghost</Button>
              <Button disabled>Disabled</Button>
            </div>
          </Card>

          <Card title="Form controls">
            <FormField label="Example task title" hint="Fabricated placeholder">
              <Input placeholder="Water the plants" />
            </FormField>
            <FormField label="Example notes">
              <Textarea rows={3} placeholder="Optional demo notes" />
            </FormField>
            <FormField label="Example priority">
              <Select
                options={[
                  { value: "low", label: "Low" },
                  { value: "medium", label: "Medium" },
                  { value: "high", label: "High" },
                ]}
                defaultValue="medium"
              />
            </FormField>
            <Checkbox
              label="Show completed demo items"
              checked={exampleChecked}
              onChange={(event) => setExampleChecked(event.target.checked)}
            />
          </Card>

          <Card title="Feedback">
            <div className="pf-gallery__row">
              <Badge>Neutral</Badge>
              <Badge tone="success">Completed</Badge>
              <Badge tone="warning">Due soon</Badge>
              <Badge tone="danger">Overdue</Badge>
            </div>
            <LoadingIndicator label="Loading demo data" />
            <EmptyState
              title="No example tasks"
              description="Fabricated empty state for the component gallery."
              action={<Button variant="secondary">Add demo task</Button>}
            />
          </Card>

          <Card title="Dialog">
            <Button onClick={() => setDialogOpen(true)}>Open example dialog</Button>
            <Dialog
              open={dialogOpen}
              title="Example dialog"
              onClose={() => setDialogOpen(false)}
            >
              <p>This dialog uses the native HTML dialog element with a focus trap.</p>
              <p>Content is fabricated for development preview only.</p>
            </Dialog>
          </Card>
        </div>
      </main>

      <footer className="pf-footer">
        <p>Component gallery — not for production planner data.</p>
      </footer>
    </div>
  );
}
