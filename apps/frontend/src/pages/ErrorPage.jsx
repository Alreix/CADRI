import { useRouteError, useNavigate, isRouteErrorResponse } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import "../styles/ErrorPage.css";


function ErrorPage() {
  const navigate = useNavigate();
  const routeError = useRouteError();

  let errorCode = "404";
  let errorTitle = "Cette page n'existe pas";
  let errorMessage =
    "La page que vous cherchez a peut-être été déplacée, renommée ou supprimée. " +
    "Vérifiez l'adresse ou retournez à l'accueil.";

  if (routeError) {
    if (isRouteErrorResponse(routeError)) {
      errorCode = String(routeError.status);
      if (routeError.status === 403) {
        errorTitle = "Accès refusé";
        errorMessage =
          "Vous n'avez pas les droits nécessaires pour accéder à cette page. " +
          "Contactez un administrateur si vous pensez qu'il s'agit d'une erreur.";
      } else if (routeError.status === 500) {
        errorTitle = "Erreur serveur";
        errorMessage =
          "Une erreur interne s'est produite. L'équipe technique a été notifiée. " +
          "Réessayez dans quelques instants ou contactez le support.";
      }
    } else {
      errorCode = "Oups";
      errorTitle = "Une erreur s'est produite";
      errorMessage =
        "Une erreur inattendue s'est produite. Actualisez la page ou revenez à l'accueil.";
    }
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