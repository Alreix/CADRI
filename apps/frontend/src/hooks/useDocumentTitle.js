import { useEffect } from "react";

// Sets the browser tab title for the current page. Screen reader users rely
// on this to know which page they landed on after a route change.
export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} — CADRI` : "CADRI";
  }, [title]);
}
