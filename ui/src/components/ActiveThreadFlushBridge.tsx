import type { MutableRefObject } from "react";

import { useActiveThreadPersistence } from "../hooks/useActiveThreadPersistence";

type Props = {
  threadId: string;
  flushRef: MutableRefObject<() => void>;
};

/** Wires flush() into App so session switches save before threadId changes. */
export function ActiveThreadFlushBridge({ threadId, flushRef }: Props) {
  const { flush } = useActiveThreadPersistence(threadId);
  flushRef.current = flush;
  return null;
}
