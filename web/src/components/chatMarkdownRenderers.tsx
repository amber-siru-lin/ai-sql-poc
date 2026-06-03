import type { ReactNode } from "react";

import { CollapsibleStep } from "./CollapsibleStep";

function flattenNode(node: ReactNode): string {
  if (node == null || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(flattenNode).join("");
  if (typeof node === "object" && "props" in node) {
    return flattenNode((node as { props: { children?: ReactNode } }).props.children);
  }
  return "";
}

function thinkingRenderer(tagLabel: string) {
  return function ThinkingBlock({ children }: { children?: ReactNode }) {
    const text = flattenNode(children).replace(/\s+/g, " ").trim();
    const preview =
      text.length > 72 ? `${text.slice(0, 72)}…` : text || "Model reasoning";
    return (
      <CollapsibleStep title={tagLabel} preview={preview}>
        {children}
      </CollapsibleStep>
    );
  };
}

/** Custom tags in assistant markdown (rehype-raw). */
export const chatMarkdownTagRenderers = {
  thinking: thinkingRenderer("Thinking"),
  think: thinkingRenderer("Thinking"),
  reasoning: thinkingRenderer("Reasoning"),
} as const;
