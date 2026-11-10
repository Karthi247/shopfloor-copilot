import React from 'react';
import Icon from './Icon';

export default function SourceCard({ source }) {
  return (
    <article className="source-card">
      <span className="source-card-icon">
        <Icon name="document" size={16} />
      </span>
      <span className="source-card-copy">
        <strong>
          {source.document_number}
          {source.revision ? ` · Rev ${String(source.revision).padStart(2, '0')}` : ''}
        </strong>
        <small>
          {source.title}
          {source.section_heading && source.section_heading !== 'Section not identified'
            ? ` · ${source.section_heading}`
            : ''}
        </small>
      </span>
      <span className="source-page">Page {source.page}</span>
    </article>
  );
}
