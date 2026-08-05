import { useEffect, useRef, useState } from "react";

const PRIMARY_LINKS = [
  { href: "/today", label: "Today" },
  { href: "/week", label: "Week" },
  { href: "/backlog", label: "Backlog" },
] as const;

const MORE_LINKS = [
  { href: "/month", label: "Month" },
  { href: "/routines", label: "Routines" },
  { href: "/schedule", label: "Schedule" },
  { href: "/maintenance", label: "Maintenance" },
  { href: "/packing", label: "Packing" },
  { href: "/settings", label: "Settings" },
] as const;

function isPrimaryActive(path: string, currentPath: string): boolean {
  if (path === "/week") {
    return currentPath === "/" || currentPath === "/week";
  }
  return currentPath === path;
}

function isMoreActive(currentPath: string): boolean {
  return MORE_LINKS.some((link) => link.href === currentPath);
}

export interface MobileBottomNavProps {
  currentPath: string;
}

export function MobileBottomNav({ currentPath }: MobileBottomNavProps) {
  const [moreOpen, setMoreOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    if (moreOpen) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else if (dialog.open) {
      dialog.close();
    }
  }, [moreOpen]);

  return (
    <>
      <nav className="pf-mobile-nav" aria-label="Mobile">
        <ul className="pf-mobile-nav__list">
          {PRIMARY_LINKS.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className="pf-mobile-nav__link"
                aria-current={
                  isPrimaryActive(link.href, currentPath) ? "page" : undefined
                }
              >
                {link.label}
              </a>
            </li>
          ))}
          <li>
            <button
              type="button"
              className="pf-mobile-nav__link pf-mobile-nav__link--button"
              aria-current={isMoreActive(currentPath) ? "page" : undefined}
              aria-expanded={moreOpen}
              aria-controls="mobile-more-menu"
              onClick={() => setMoreOpen(true)}
            >
              More
            </button>
          </li>
        </ul>
      </nav>

      <dialog
        ref={dialogRef}
        id="mobile-more-menu"
        className="pf-mobile-more"
        onClose={() => setMoreOpen(false)}
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            setMoreOpen(false);
          }
        }}
      >
        <div className="pf-mobile-more__panel" role="document">
          <header className="pf-mobile-more__header">
            <h2>More</h2>
            <button
              type="button"
              className="pf-mobile-more__close"
              onClick={() => setMoreOpen(false)}
            >
              Close
            </button>
          </header>
          <ul className="pf-mobile-more__links">
            {MORE_LINKS.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  className="pf-mobile-more__link"
                  aria-current={currentPath === link.href ? "page" : undefined}
                  onClick={() => setMoreOpen(false)}
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </dialog>
    </>
  );
}
