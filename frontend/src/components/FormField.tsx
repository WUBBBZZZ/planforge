import type { InputHTMLAttributes, ReactNode } from "react";

export interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
  children?: ReactNode;
}

export function FormField({
  label,
  hint,
  error,
  id,
  children,
  className = "",
  ...props
}: FormFieldProps) {
  const fieldId = id ?? `field-${label.replace(/\s+/g, "-").toLowerCase()}`;

  return (
    <div className={`pf-form-field ${className}`.trim()}>
      <label htmlFor={fieldId}>{label}</label>
      {children ?? <input id={fieldId} {...props} />}
      {hint ? <p className="pf-form-field__hint">{hint}</p> : null}
      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
