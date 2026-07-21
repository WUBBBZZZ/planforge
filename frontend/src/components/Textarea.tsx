import type { TextareaHTMLAttributes } from "react";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  hasError?: boolean;
}

export function Textarea({
  className = "",
  hasError = false,
  ...props
}: TextareaProps) {
  return (
    <textarea
      className={`pf-textarea ${hasError ? "pf-textarea--error" : ""} ${className}`.trim()}
      {...props}
    />
  );
}
