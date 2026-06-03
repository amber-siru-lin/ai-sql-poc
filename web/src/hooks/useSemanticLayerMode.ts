import { useCallback, useEffect, useState } from "react";

import {
  DEFAULT_SEMANTIC_LAYER,
  type SemanticLayerMode,
  type SemanticLayerStatus,
} from "../config";

const STORAGE_KEY = "ai-sql-poc-semantic-layer";

export function useSemanticLayerMode(apiStatus: SemanticLayerStatus | null) {
  const [mode, setModeState] = useState<SemanticLayerMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "off" || stored === "wren" || stored === "cortex") {
      return stored;
    }
    return DEFAULT_SEMANTIC_LAYER;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  const setMode = useCallback(
    (next: SemanticLayerMode) => {
      if (next === "wren" && apiStatus && !apiStatus.wren_ready) {
        return;
      }
      if (next === "cortex" && apiStatus && !apiStatus.cortex_ready) {
        return;
      }
      setModeState(next);
    },
    [apiStatus],
  );

  return { mode, setMode };
}
