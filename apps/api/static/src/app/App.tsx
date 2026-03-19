import { Route, Router } from "@solidjs/router";
import { PublicPage } from "../pages/PublicPage";
import { AuthPage } from "../pages/AuthPage";
import { ChatPage } from "../pages/ChatPage";

export function App() {
  return (
    <Router>
      <Route path="/" component={PublicPage} />
      <Route path="/auth" component={AuthPage} />
      <Route path="/chat" component={ChatPage} />
    </Router>
  );
}

