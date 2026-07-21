import type { InputHTMLAttributes } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

export function Input({ className = "", hasError = false, ...props }: InputProps) {
  return (
    <input
      className={`pf-input ${hasError ? "pf-input--error" : ""} ${className}`.trim()}
      {...props}
    />
  );
}
