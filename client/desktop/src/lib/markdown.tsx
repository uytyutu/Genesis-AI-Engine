import type { ReactNode } from "react";

/** Lightweight markdown: fenced code blocks + inline code + bold. */
export function MessageBody({ text }: { text: string }) {
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="md">
      {parts.map((part, i) => {
        if (part.startsWith("```") && part.endsWith("```")) {
          const inner = part.slice(3, -3);
          const nl = inner.indexOf("\n");
          const code = nl >= 0 ? inner.slice(nl + 1) : inner;
          return (
            <pre key={i} className="md__code">
              <code>{code.trimEnd()}</code>
            </pre>
          );
        }
        return <span key={i}>{renderInline(part)}</span>;
      })}
    </div>
  );
}

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const re = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let k = 0;

  while ((match = re.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index));
    }
    const token = match[0];
    if (token.startsWith("`")) {
      nodes.push(
        <code key={k++} className="md__inline">
          {token.slice(1, -1)}
        </code>,
      );
    } else {
      nodes.push(<strong key={k++}>{token.slice(2, -2)}</strong>);
    }
    last = match.index + token.length;
  }

  if (last < text.length) nodes.push(text.slice(last));
  return nodes.length ? nodes : [text];
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
