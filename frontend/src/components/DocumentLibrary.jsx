import React, { useMemo, useState } from 'react';
import Icon from './Icon';
import './DocumentLibrary.css';

function categoryFor(number = '') {
  if (number.startsWith('MNT-')) return 'Maintenance';
  if (number.startsWith('QC-')) return 'Quality';
  if (number.startsWith('SAF-')) return 'Safety';
  return 'Procedure';
}

export default function DocumentLibrary({ documents, loading, error }) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const query = search.trim().toLowerCase();
  const filtered = useMemo(
    () =>
      documents.filter((document) => {
        const matchesSearch =
          `${document.document_number} ${document.title} ${document.filename} Rev ${document.revision} ${categoryFor(document.document_number)}`
            .toLowerCase()
            .includes(query);
        return (
          matchesSearch &&
          (statusFilter === 'all' ||
            (statusFilter === 'current' ? document.is_current : !document.is_current))
        );
      }),
    [documents, query, statusFilter],
  );
  const currentCount = documents.filter((document) => document.is_current).length;

  return (
    <section className="page-container document-library">
      <div className="page-heading">
        <div>
          <span className="page-eyebrow">KNOWLEDGE BASE</span>
          <h2>Document Library</h2>
          <p>Approved procedures and manuals indexed for ShopFloor Copilot.</p>
        </div>
        <div className="document-summary">
          <strong>{documents.length}</strong>
          <span>indexed revisions</span>
        </div>
      </div>
      <div className="library-toolbar">
        <label className="library-search">
          <Icon name="search" size={17} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search documents"
            aria-label="Search documents"
          />
        </label>
        <div
          className="status-filters"
          role="group"
          aria-label="Filter document revision status"
        >
          {[
            ['all', 'All'],
            ['current', 'Current'],
            ['superseded', 'Superseded'],
          ].map(([value, label]) => (
            <button
              key={value}
              className={statusFilter === value ? 'selected' : ''}
              onClick={() => setStatusFilter(value)}
              aria-pressed={statusFilter === value}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="library-summary-line">
        <span>
          {loading
            ? 'Loading indexed documents…'
            : `${filtered.length} of ${documents.length} revisions`}
        </span>
        <span>{currentCount} current</span>
      </div>
      {loading && (
        <div className="library-state">
          <span className="spinner light" />
          Loading documents…
        </div>
      )}
      {!loading && error && (
        <div className="library-state error-state" role="alert">
          <Icon name="safety" />
          <span>
            <strong>Couldn’t load documents</strong>
            <small>{error}</small>
          </span>
        </div>
      )}
      {!loading && !error && documents.length === 0 && (
        <div className="library-state">No indexed documents were found.</div>
      )}
      {!loading && !error && documents.length > 0 && filtered.length === 0 && (
        <div className="library-state">No documents match those filters.</div>
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="document-table-wrap">
          <table className="document-table">
            <thead>
              <tr>
                <th>DOCUMENT</th>
                <th>CATEGORY</th>
                <th>REVISION</th>
                <th>EFFECTIVE DATE</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((document) => (
                <tr key={`${document.filename}-${document.revision}`}>
                  <td data-label="Document">
                    <div className="table-document">
                      <span className="table-document-icon">
                        <Icon name="document" size={17} />
                      </span>
                      <span>
                        <strong>{document.title}</strong>
                        <small>{document.document_number}</small>
                        <small className="document-filename">{document.filename}</small>
                      </span>
                    </div>
                  </td>
                  <td data-label="Category">
                    <span className="category-label">
                      {categoryFor(document.document_number)}
                    </span>
                  </td>
                  <td data-label="Revision">
                    <span className="revision-label">
                      Rev {String(document.revision ?? '—').padStart(2, '0')}
                    </span>
                    {!document.is_current && document.superseded_by != null && (
                      <small className="superseded-detail">
                        Replaced by Rev{' '}
                        {String(document.superseded_by).padStart(2, '0')}
                      </small>
                    )}
                  </td>
                  <td data-label="Effective date">
                    {document.effective_date &&
                    document.effective_date !== 'Unknown' ? (
                      document.effective_date
                    ) : (
                      <span className="metadata-unavailable">Not specified</span>
                    )}
                  </td>
                  <td data-label="Status">
                    <span
                      className={`document-status ${document.is_current ? 'current' : 'superseded'}`}
                    >
                      <i />
                      {document.is_current ? 'Current' : 'Superseded'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
