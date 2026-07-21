import { useEffect, useId, useRef, type ReactNode } from "react";

import { Button } from "./Button";

export interface DialogProps {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
}

export function Dialog({ open, title, children, onClose }: DialogProps) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    const handleCancel = (event: Event) => {
      event.preventDefault();
      onClose();
    };

    dialog.addEventListener("cancel", handleCancel);
    return () => dialog.removeEventListener("cancel", handleCancel);
  }, [onClose]);

  return (
    <dialog
      ref={dialogRef}
      className="pf-dialog"
      aria-labelledby={titleId}
      onClose={onClose}
    >
      <header className="pf-dialog__header">
        <h2 id={titleId}>{title}</h2>
        <Button variant="ghost" onClick={onClose} aria-label="Close dialog">
          Close
        </Button>
      </header>
      <div className="pf-dialog__body">{children}</div>
    </dialog>
  );
}
