/** Reconstruct text independently of how TCP/WebSocket split output frames. */
export function transcriptText(entries) {
  return entries.map(entry => {
    if (entry.kind === 'output') return Array.isArray(entry.tokens) ? entry.tokens.map(token => token.text).join('') : entry.text;
    return entry.text + (entry.text.endsWith('\n') ? '' : '\n');
  }).join('');
}

export function searchTranscript(text, query) {
  const needle = query.trim().toLocaleLowerCase();
  if (!needle) return [];
  return text.split('\n').flatMap((line, index) => line.toLocaleLowerCase().includes(needle) ? [{line: index + 1, text: line}] : []);
}
