// Root component: wraps the whole app with authentication state, then renders the router.
import AppRouter from "./router/AppRouter";
import AuthProvider from "./contexts/AuthContext";

function App() {
  return (
    // AuthProvider must wrap AppRouter so every page can access the current user via context.
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}

export default App;