import type { SelectHTMLAttributes } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
  hasError?: boolean;
}

export function Select({
  options,
  className = "",
  hasError = false,
  ...props
}: SelectProps) {
  return (
    <select
      className={`pf-select ${hasError ? "pf-select--error" : ""} ${className}`.trim()}
      {...props}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
