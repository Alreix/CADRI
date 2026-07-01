// Application entry point: mounts the root React component into the DOM.
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

// React.StrictMode runs extra checks/warnings in development only (no effect in production).
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
