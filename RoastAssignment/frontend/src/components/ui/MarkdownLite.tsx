import { Box, ListItem, OrderedList, Text, UnorderedList } from '@chakra-ui/react';
import { Fragment } from 'react';

function renderInline(text: string, keyPrefix: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <Text as="b" key={`${keyPrefix}-${i}`}>
        {part.slice(2, -2)}
      </Text>
    ) : (
      <Fragment key={`${keyPrefix}-${i}`}>{part}</Fragment>
    )
  );
}

type Block =
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'p'; lines: string[] };

const BULLET_RE = /^[-*]\s+(.*)$/;
const NUMBERED_RE = /^\d+[.)]\s+(.*)$/;

/**
 * Groups raw lines into list/paragraph blocks. Consecutive numbered or
 * bulleted lines are merged into ONE list even when separated by blank
 * lines (the AI always puts a blank line between list items) — without
 * this, each item would render as its own single-item <OrderedList>,
 * which always restarts numbering at 1.
 */
function groupIntoBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  let paragraphLines: string[] = [];

  const flushParagraph = () => {
    if (paragraphLines.length > 0) {
      blocks.push({ type: 'p', lines: paragraphLines });
      paragraphLines = [];
    }
  };

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      continue;
    }

    const bulletMatch = BULLET_RE.exec(line);
    const numberedMatch = bulletMatch ? null : NUMBERED_RE.exec(line);

    if (bulletMatch) {
      flushParagraph();
      const last = blocks[blocks.length - 1];
      if (last?.type === 'ul') {
        last.items.push(bulletMatch[1]);
      } else {
        blocks.push({ type: 'ul', items: [bulletMatch[1]] });
      }
    } else if (numberedMatch) {
      flushParagraph();
      const last = blocks[blocks.length - 1];
      if (last?.type === 'ol') {
        last.items.push(numberedMatch[1]);
      } else {
        blocks.push({ type: 'ol', items: [numberedMatch[1]] });
      }
    } else {
      paragraphLines.push(line);
    }
  }
  flushParagraph();

  return blocks;
}

interface MarkdownLiteProps {
  text: string;
  color?: string;
}

/** Minimal markdown rendering for AI-generated text: paragraphs, bullet/numbered lists, **bold**. */
export function MarkdownLite({ text, color = 'gray.700' }: MarkdownLiteProps): JSX.Element {
  const blocks = groupIntoBlocks(text);

  return (
    <Box color={color} fontSize="md">
      {blocks.map((block, blockIndex) => {
        if (block.type === 'ul') {
          return (
            <UnorderedList key={blockIndex} mb={3} spacing={2} pl={4}>
              {block.items.map((item, i) => (
                <ListItem key={i} lineHeight="tall">
                  {renderInline(item, `${blockIndex}-${i}`)}
                </ListItem>
              ))}
            </UnorderedList>
          );
        }

        if (block.type === 'ol') {
          return (
            <OrderedList key={blockIndex} mb={3} spacing={2} pl={4}>
              {block.items.map((item, i) => (
                <ListItem key={i} lineHeight="tall">
                  {renderInline(item, `${blockIndex}-${i}`)}
                </ListItem>
              ))}
            </OrderedList>
          );
        }

        return (
          <Text key={blockIndex} mb={3} whiteSpace="pre-wrap" lineHeight="tall">
            {renderInline(block.lines.join('\n'), `${blockIndex}`)}
          </Text>
        );
      })}
    </Box>
  );
}
