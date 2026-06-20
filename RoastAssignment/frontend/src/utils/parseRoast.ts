export type RoastSectionKey = 'good' | 'roast' | 'overall' | 'other';

export interface RoastSection {
  key: RoastSectionKey;
  title: string;
  content: string;
}

const SECTION_MATCHERS: Array<{ key: RoastSectionKey; pattern: RegExp }> = [
  { key: 'good', pattern: /good stuff|what(?:'s| is)? working|strengths?/i },
  { key: 'roast', pattern: /roast|critique|issues?|problems?|could improve/i },
  { key: 'overall', pattern: /overall|verdict|summary|conclusion/i },
];

function classify(title: string): RoastSectionKey {
  for (const { key, pattern } of SECTION_MATCHERS) {
    if (pattern.test(title)) return key;
  }
  return 'other';
}

const HEADING_RE = /^#{1,3}\s*(.+)$/;

/**
 * Splits the AI roast's markdown-ish text into sections by `#`/`##`/`###`
 * headings, classifying each by title into good/roast/overall/other. Falls
 * back to a single 'other' section (or none, for empty text) if the model
 * didn't follow the requested heading structure — older evaluations
 * generated before the prompt mandated sections won't have them.
 */
export function parseRoastSections(text: string): RoastSection[] {
  if (!text) return [];

  const lines = text.split('\n');
  const sections: RoastSection[] = [];
  let current: RoastSection | null = null;

  for (const line of lines) {
    const match = line.match(HEADING_RE);
    if (match) {
      if (current) sections.push(current);
      const title = match[1].replace(/[*_]/g, '').trim();
      current = { key: classify(title), title, content: '' };
    } else if (current) {
      current.content += (current.content ? '\n' : '') + line;
    } else {
      current = { key: 'other', title: '', content: line };
    }
  }
  if (current) sections.push(current);

  return sections.map((s) => ({ ...s, content: s.content.trim() })).filter((s) => s.content);
}
