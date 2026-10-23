/**
 * Renders the inline bold markers the assistant commonly returns without
 * pulling in a full Markdown renderer.
 */
export function FormattedText({ text, className }: { text: string; className?: string }) {
  return (
    <p className={className}>
      {text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={index}>{part.slice(2, -2)}</strong>
        ) : (
          <span key={index}>{part}</span>
        )
      )}
    </p>
  );
}
