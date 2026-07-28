import { Button } from "./Button";

export interface PeriodNavProps {
  label: string;
  onPrevious: () => void;
  onNext: () => void;
  onToday: () => void;
  previousLabel?: string;
  nextLabel?: string;
  todayLabel?: string;
}

export function PeriodNav({
  label,
  onPrevious,
  onNext,
  onToday,
  previousLabel = "Previous",
  nextLabel = "Next",
  todayLabel = "Today",
}: PeriodNavProps) {
  return (
    <div className="pf-period-nav">
      <div className="pf-period-nav__controls">
        <Button variant="secondary" onClick={onPrevious}>
          {previousLabel}
        </Button>
        <Button variant="secondary" onClick={onToday}>
          {todayLabel}
        </Button>
        <Button variant="secondary" onClick={onNext}>
          {nextLabel}
        </Button>
      </div>
      <p className="pf-period-nav__label">{label}</p>
    </div>
  );
}
