import React from 'react';

function renderInline(text, keyPrefix) {
  const tokens = text.split(/(\*\*[^*]+\*\*|(?<!\*)\*[^*\n]+\*|`[^`\n]+`)/g);
  return tokens.map((token, index) => {
    const key = `${keyPrefix}-${index}`;
    if (token.startsWith('**') && token.endsWith('**'))
      return <strong key={key}>{token.slice(2, -2)}</strong>;
    if (token.startsWith('*') && token.endsWith('*'))
      return <em key={key}>{token.slice(1, -1)}</em>;
    if (token.startsWith('`') && token.endsWith('`'))
      return <code key={key}>{token.slice(1, -1)}</code>;
    return token;
  });
}

const isListItem = (line) => /^\s*(?:[-*]|\d+\.)\s+/.test(line);
const isOrdered = (line) => /^\s*\d+\.\s+/.test(line);

export default function AnswerMarkdown({ children }) {
  const lines = String(children || '')
    .replace(/\r\n?/g, '\n')
    .split('\n');
  const blocks = [];
  let paragraph = [];
  let list = [];
  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: 'paragraph', lines: paragraph });
    paragraph = [];
  };
  const flushList = () => {
    if (list.length)
      blocks.push({ type: isOrdered(list[0]) ? 'ol' : 'ul', lines: list });
    list = [];
  };

  lines.forEach((line) => {
    if (!line.trim()) {
      flushParagraph();
      flushList();
    } else if (isListItem(line)) {
      flushParagraph();
      list.push(line.replace(/^\s*(?:[-*]|\d+\.)\s+/, ''));
    } else {
      flushList();
      paragraph.push(line);
    }
  });
  flushParagraph();
  flushList();

  return (
    <div className="answer-text">
      {blocks.map((block, index) => {
        if (block.type === 'ul' || block.type === 'ol') {
          const List = block.type;
          return (
            <List key={index}>
              {block.lines.map((line, itemIndex) => (
                <li key={itemIndex}>{renderInline(line, `${index}-${itemIndex}`)}</li>
              ))}
            </List>
          );
        }
        return (
          <p key={index}>
            {block.lines.map((line, lineIndex) => (
              <React.Fragment key={lineIndex}>
                {lineIndex > 0 && <br />}
                {renderInline(line, `${index}-${lineIndex}`)}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}
