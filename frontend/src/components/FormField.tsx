import {
  cloneElement,
  isValidElement,
  useId,
  type InputHTMLAttributes,
  type ReactElement,
  type ReactNode,
} from "react";

export interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
  children?: ReactNode;
}

function assignControlId(children: ReactNode, fieldId: string): ReactNode {
  if (!isValidElement(children)) {
    return children;
  }
  const element = children as ReactElement<{ id?: string }>;
  return cloneElement(element, {
    id: element.props.id ?? fieldId,
  });
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
  const generatedId = useId();
  const fieldId = id ?? generatedId;

  return (
    <div className={`pf-form-field ${className}`.trim()}>
      <label htmlFor={fieldId}>{label}</label>
      {children ? (
        assignControlId(children, fieldId)
      ) : (
        <input id={fieldId} {...props} />
      )}
      {hint ? <p className="pf-form-field__hint">{hint}</p> : null}
      {error ? (
        <p className="pf-form-field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
