import { BacklogPage } from "./pages/BacklogPage";
import { DevComponentsPage } from "./pages/DevComponentsPage";
import { MonthPage } from "./pages/MonthPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RoutinesPage } from "./pages/RoutinesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TodayPage } from "./pages/TodayPage";
import { WeekPage } from "./pages/WeekPage";

const KNOWN_PATHS = new Set([
  "/",
  "/week",
  "/today",
  "/month",
  "/backlog",
  "/routines",
  "/settings",
  "/dev/components",
]);

function App() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";

  if (!KNOWN_PATHS.has(path)) {
    return <NotFoundPage />;
  }

  if (path === "/dev/components") {
    return <DevComponentsPage />;
  }

  if (path === "/today") {
    return <TodayPage />;
  }

  if (path === "/month") {
    return <MonthPage />;
  }

  if (path === "/backlog") {
    return <BacklogPage />;
  }

  if (path === "/routines") {
    return <RoutinesPage />;
  }

  if (path === "/settings") {
    return <SettingsPage />;
  }

  return <WeekPage />;
}

export default App;
