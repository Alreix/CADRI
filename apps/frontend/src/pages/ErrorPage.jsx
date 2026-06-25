import { useRouteError, useNavigate, isRouteErrorResponse } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import "../styles/ErrorPage.css";


function ErrorPage({ code }) {
  const navigate = useNavigate();

  let routeError;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    routeError = useRouteError();
  } catch {
    // useRouteError() throws when rendered outside a data router (e.g. when
    // ProtectedRoute renders <ErrorPage code={403} /> directly as a regular
    // child, or in tests using MemoryRouter). In that case there is no route
    // error to read, so we simply fall back to the `code` prop below.
    routeError = undefined;
  }

  let errorCode = "404";
  let errorTitle = "Cette page n'existe pas";
  let errorMessage =
    "La page que vous cherchez a peut-être été déplacée, renommée ou supprimée. " +
    "Vérifiez l'adresse ou retournez à l'accueil.";

  const applyStatus = (status) => {
    errorCode = String(status);
    if (status === 403) {
      errorTitle = "Accès refusé";
      errorMessage =
        "Vous n'avez pas les droits nécessaires pour accéder à cette page. " +
        "Contactez un administrateur si vous pensez qu'il s'agit d'une erreur.";
    } else if (status === 500) {
      errorTitle = "Erreur serveur";
      errorMessage =
        "Une erreur interne s'est produite. L'équipe technique a été notifiée. " +
        "Réessayez dans quelques instants ou contactez le support.";
    }
  };

  if (routeError) {
    if (isRouteErrorResponse(routeError)) {
      applyStatus(routeError.status);
    } else {
      errorCode = "Oups";
      errorTitle = "Une erreur s'est produite";
      errorMessage =
        "Une erreur inattendue s'est produite. Actualisez la page ou revenez à l'accueil.";
    }
  } else if (code) {
    applyStatus(code);
  }

  const errorLabel = `ERREUR ${errorCode} — ${
    errorCode === "404" ? "PAGE INTROUVABLE" :
    errorCode === "403" ? "ACCÈS REFUSÉ" :
    errorCode === "500" ? "ERREUR SERVEUR" : "ERREUR"
  }`;

  return (
    <AuthLayout>
      <div className="error-card">
        <span className="error-code">{errorCode}</span>
        <p className="error-label">{errorLabel}</p>
        <p className="error-title">{errorTitle}</p>
        <p className="error-message">{errorMessage}</p>
        <a href="/" className="error-btn">Retour à l'accueil</a>
      </div>
    </AuthLayout>
  );
}

export default ErrorPage;