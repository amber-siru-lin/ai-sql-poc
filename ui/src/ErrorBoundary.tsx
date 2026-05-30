import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

/** Surface React crashes instead of a blank page. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("UI error:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif", maxWidth: 720 }}>
          <h1>Something went wrong</h1>
          <p style={{ color: "#57534e" }}>
            The chat UI hit an error. Check the browser console and that the API is running on
            port 8000.
          </p>
          <pre
            style={{
              background: "#fef3c7",
              padding: "1rem",
              borderRadius: 8,
              overflow: "auto",
              fontSize: "0.85rem",
            }}
          >
            {this.state.error.message}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
