import React from "react";

// Minimal inline Markdown renderer: **bold**, *italic*, plain text.
function parseInline(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+?\*\*|\*[^*]+?\*)/);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return part || null;
  });
}

type Block =
  | { type: "h1"; text: string }
  | { type: "spoiler"; text: string }
  | { type: "h2"; text: string }
  | { type: "p"; text: string }
  | { type: "footer"; text: string };

const FOOTER_RE = /^(written by|reviewed by|edited by)\b/i;

function parseMarkdown(md: string): Block[] {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let buf: string[] = [];
  let seenH1 = false;
  let seenSpoiler = false;

  const flush = () => {
    if (!buf.length) return;
    const para = buf.join(" ").trim();
    if (!para) { buf = []; return; }
    if (FOOTER_RE.test(para)) {
      blocks.push({ type: "footer", text: para });
    } else {
      blocks.push({ type: "p", text: para });
    }
    buf = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const stripped = line.trim();

    if (!stripped) { flush(); continue; }

    if (stripped.startsWith("# ") && !stripped.startsWith("## ")) {
      flush();
      if (!seenH1) { seenH1 = true; blocks.push({ type: "h1", text: stripped.slice(2).trim() }); }
      continue;
    }

    if (stripped.startsWith("## ")) {
      flush();
      blocks.push({ type: "h2", text: stripped.slice(3).trim() });
      continue;
    }

    // Italic spoiler line (whole line is *text*, not **bold**)
    if (!seenSpoiler && !blocks.filter(b => b.type === "p" || b.type === "h2").length
      && stripped.startsWith("*") && stripped.endsWith("*") && !stripped.startsWith("**")) {
      seenSpoiler = true;
      blocks.push({ type: "spoiler", text: stripped.slice(1, -1).trim() });
      continue;
    }

    buf.push(line);
  }
  flush();
  return blocks;
}

export function ReviewBody({ markdown }: { markdown: string }) {
  const blocks = parseMarkdown(markdown);
  let firstPara = true;

  return (
    <div className="review-body">
      {blocks.map((block, i) => {
        if (block.type === "h1") return null; // page already has an H1
        if (block.type === "spoiler") return null; // rendered outside
        if (block.type === "footer") return (
          <p key={i} className="review-body__footer">{block.text}</p>
        );
        if (block.type === "h2") return (
          <h2 key={i} className="review-body__h2">
            <span className="review-body__h2-rule" aria-hidden="true" />
            {parseInline(block.text)}
          </h2>
        );
        // p
        const isLede = firstPara;
        if (firstPara) firstPara = false;
        return (
          <p key={i} className={isLede ? "review-body__p review-body__p--lede" : "review-body__p"}>
            {parseInline(block.text)}
          </p>
        );
      })}
    </div>
  );
}
