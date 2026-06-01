import type { MutableRefObject } from "react";

import { useActiveThreadPersistence } from "../hooks/useActiveThreadPersistence";

type Props = {
  threadId: string;
  flushRef: MutableRefObject<() => void>;
  copilotOwnerThreadIdRef: MutableRefObject<string>;
};

/** Wires flush() into App so session switches save before threadId changes. */
export function ActiveThreadFlushBridge({
  threadId,
  flushRef,
  copilotOwnerThreadIdRef,
}: Props) {
  const { flush } = useActiveThreadPersistence(threadId, copilotOwnerThreadIdRef);
  flushRef.current = flush;
  return null;
}
