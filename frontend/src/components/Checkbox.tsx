import type { InputHTMLAttributes } from "react";

export interface CheckboxProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type"
> {
  label: string;
}

export function Checkbox({ label, id, className = "", ...props }: CheckboxProps) {
  const inputId = id ?? `checkbox-${label.replace(/\s+/g, "-").toLowerCase()}`;

  return (
    <label className={`pf-checkbox ${className}`.trim()} htmlFor={inputId}>
      <input id={inputId} type="checkbox" {...props} />
      <span>{label}</span>
    </label>
  );
}
