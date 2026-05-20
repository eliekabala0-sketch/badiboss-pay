import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { bootstrapAuth } from "./auth";
import "./index.css";

bootstrapAuth();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter basename={import.meta.env.VITE_BASE_PATH ?? "/"}>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
