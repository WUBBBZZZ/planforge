import type { ReactNode } from "react";

export type BadgeTone = "neutral" | "success" | "warning" | "danger";

export interface BadgeProps {
  children: ReactNode;
  tone?: BadgeTone;
}

export function Badge({ children, tone = "neutral" }: BadgeProps) {
  return <span className={`pf-badge pf-badge--${tone}`}>{children}</span>;
}
