export interface LoadingIndicatorProps {
  label?: string;
}

export function LoadingIndicator({ label = "Loading" }: LoadingIndicatorProps) {
  return (
    <div className="pf-loading" role="status" aria-live="polite">
      <span className="pf-loading__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
