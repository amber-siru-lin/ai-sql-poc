import type { MutableRefObject } from "react";

import { useEditorThreadPersistence } from "../hooks/useEditorThreadPersistence";

type Props = {
  threadId: string;
  flushRef: MutableRefObject<() => void>;
  editorOwnerThreadIdRef: MutableRefObject<string>;
};

export function EditorActiveThreadFlushBridge({
  threadId,
  flushRef,
  editorOwnerThreadIdRef,
}: Props) {
  const { flush } = useEditorThreadPersistence(threadId, editorOwnerThreadIdRef);
  flushRef.current = flush;
  return null;
}
