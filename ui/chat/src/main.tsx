import React from "react";
import ReactDOM from "react-dom/client";
import { FluentProvider } from "@fluentui/react-components";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import { TenantProvider } from "./shell/TenantContext";
import { 法人LightTheme } from "./theme/corporate";

const qc = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <FluentProvider theme={法人LightTheme} style={{ minHeight: "100vh" }}>
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <TenantProvider>
            <App />
          </TenantProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </FluentProvider>
  </React.StrictMode>,
);
