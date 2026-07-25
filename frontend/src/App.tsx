import { DevComponentsPage } from "./pages/DevComponentsPage";
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

  return <WeekPage />;
}

export default App;
