import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Amplify } from "aws-amplify";
import { Authenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { ErrorBoundary } from "./ErrorBoundary";
import "./index.css";
import App from "./App.tsx";

function hasAuthConfig(outputs: unknown): boolean {
  if (!outputs || typeof outputs !== "object") return false;
  const auth = (outputs as { auth?: unknown }).auth;
  return Boolean(auth && typeof auth === "object");
}

void (async () => {
  let outputs: unknown;
  try {
    const mod = await import("../amplify_outputs.json");
    outputs = mod.default ?? mod;
    Amplify.configure(outputs);
  } catch {
    console.warn(
      "amplify_outputs.json not found — run `npx ampx sandbox` in web/ for Cognito config",
    );
  }

  const useAuth =
    import.meta.env.VITE_REQUIRE_AUTH === "true" && hasAuthConfig(outputs);

  const tree = (
    <ErrorBoundary>
      {useAuth ? (
        <Authenticator>
          <App />
        </Authenticator>
      ) : (
        <App />
      )}
    </ErrorBoundary>
  );

  createRoot(document.getElementById("root")!).render(
    <StrictMode>{tree}</StrictMode>,
  );
})();
