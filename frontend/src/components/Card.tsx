import type { HTMLAttributes, ReactNode } from "react";

export interface CardProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
  title?: string;
}

export function Card({ children, title, className = "", ...props }: CardProps) {
  return (
    <section className={`pf-card ${className}`.trim()} {...props}>
      {title ? <h2 className="pf-card__title">{title}</h2> : null}
      <div className="pf-card__body">{children}</div>
    </section>
  );
}
