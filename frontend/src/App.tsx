import { BacklogPage } from "./pages/BacklogPage";
import { DevComponentsPage } from "./pages/DevComponentsPage";
import { MonthPage } from "./pages/MonthPage";
import { RoutinesPage } from "./pages/RoutinesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TodayPage } from "./pages/TodayPage";
import { WeekPage } from "./pages/WeekPage";

function App() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";

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
