export function readFileAsText(file: File): Promise<string> {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload  = () => { if (typeof r.result !== 'string') { rej(new Error('Not text')); return; } res(r.result); };
    r.onerror = () => rej(r.error || new Error('Read failed'));
    r.readAsText(file);
  });
}

export function parseNotebookParameters(text: string): Record<string, string | number | boolean> {
  const nb = JSON.parse(text) as {
    cells?: Array<{ cell_type?: string; metadata?: { tags?: string[] }; source?: string[] }>;
  };
  const fallbackCellRegex = /^\s*((?:param_|conf_)[A-Za-z0-9_]*)\s*(?:<-|=)\s*(.+?)\s*$/;

  function stripComment(line: string): string {
    let inString: string | null = null;
    for (let index = 0; index < line.length; index += 1) {
      const char = line[index];
      if (inString) {
        if (char === inString) inString = null;
        continue;
      }
      if (char === '"' || char === "'") { inString = char; continue; }
      if (char === '#') { return line.slice(0, index).trimEnd(); }
    }
    return line;
  }

  let cell = nb.cells?.find(
    (c) => c.cell_type === 'code' && Array.isArray(c.metadata?.tags) && c.metadata!.tags!.includes('parameters'),
  );
  if (!cell) {
    cell = nb.cells?.find(
      (c) => c.cell_type === 'code' && c.source?.some((line) => fallbackCellRegex.test(stripComment(line))),
    );
  }
  if (!cell?.source?.length) return {};

  const out: Record<string, string | number | boolean> = {};
  const re  = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:<-|=)\s*(.+?)\s*$/;
  cell.source.forEach((raw) => {
    const line = stripComment(raw).trim();
    if (!line || line.startsWith('#')) return;
    const m = line.match(re);
    if (!m) return;
    const [, key, vRaw] = m;
    let v: string | number | boolean = vRaw;
    if (/^[-+]?\d+(?:\.\d+)?$/.test(vRaw)) {
      v = Number(vRaw);
    } else if (/^(true|false)$/i.test(vRaw)) {
      v = vRaw.toLowerCase() === 'true';
    } else {
      const stripped = vRaw.replace(/^['"]|['"]$/g, '');
      if (/^(true|false)$/i.test(stripped)) {
        v = stripped.toLowerCase() === 'true';
      } else {
        v = stripped;
      }
    }
    out[key] = v;
  });
  return out;
}

export function downloadResultFile(filename: string, b64: string): void {
  const bytes = window.atob(b64);
  const arr   = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  const url = URL.createObjectURL(new Blob([arr]));
  const a   = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}
