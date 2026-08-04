import { useState } from "react";

import { todayIsoLocal } from "../lib/dates";
import { useNarrowViewport } from "../lib/viewport";
import { CaptureModal } from "./CaptureModal";

export interface MobileCaptureFabProps {
  onCreated?: () => void;
}

export function MobileCaptureFab({ onCreated }: MobileCaptureFabProps) {
  const isNarrow = useNarrowViewport();
  const [open, setOpen] = useState(false);

  if (!isNarrow) {
    return null;
  }

  const handleCreated = () => {
    if (onCreated) {
      onCreated();
    } else {
      window.location.reload();
    }
  };

  return (
    <>
      <button
        type="button"
        className="pf-mobile-fab"
        aria-label="Capture"
        onClick={() => setOpen(true)}
      >
        +
      </button>
      <CaptureModal
        open={open}
        onClose={() => setOpen(false)}
        onCreated={handleCreated}
        defaultDueDate={todayIsoLocal()}
      />
    </>
  );
}
