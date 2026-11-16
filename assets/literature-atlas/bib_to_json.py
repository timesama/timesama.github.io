#!/usr/bin/env python3

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import bibtexparser
from bibtexparser.bparser import BibTexParser
from pylatexenc.latex2text import LatexNodes2Text

LATEX = LatexNodes2Text()
RQ = {'RQ1': 'Morphology and dynamics', 'RQ2': 'Comparison with other techniques',
      'RQ3': 'Methods and observables', 'RQ4': 'Fitting and computational difficulties',
      'RQ5': 'Theoretical and experimental second moments'}
MANUAL = {'group', 'kind', 'material', 'materials', 'tech', 'methods', 'keywords',
          'rq', 'rq_categories', 'm2', 'notes', 'extractable_data', 'classification_basis',
          'title', 'authors', 'author_objects', 'author_surnames', 'authors_display',
          'language', 'original_title', 'original_authors', 'journal_group'}


def text(value):
    return ' '.join(LATEX.latex_to_text(str(value or '')).split())


def doi(value):
    value = urllib.parse.unquote(str(value or '').strip())
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value, flags=re.I)
    return value.lower() if re.fullmatch(r'10\.\d{4,9}/\S+', value) else None


def split_top(value, separator):
    """Split BibTeX names only outside braces (including corporate authors)."""
    depth, start, result = 0, 0, []
    for i, char in enumerate(value):
        if char == '{': depth += 1
        elif char == '}': depth -= 1
        if depth == 0 and value.startswith(separator, i):
            result.append(value[start:i].strip())
            start = i + len(separator)
    result.append(value[start:].strip())
    return [part for part in result if part]


def authors(value):
    result = []
    for name in split_top(value, ' and '):
        parts = split_top(name, ',')
        if name.startswith('{') and name.endswith('}'):
            given, family = '', text(name)
        elif len(parts) >= 2:
            family = text(parts[0])
            given = text(parts[-1])
            if len(parts) == 3: family += ', ' + text(parts[1])
        else:
            words = text(name).split()
            boundary = len(words) - 1
            for i, word in enumerate(words[:-1]):
                if word[0].islower():
                    boundary = i
                    break
            given, family = ' '.join(words[:boundary]), ' '.join(words[boundary:])
        result.append({'given': given, 'family': family})
    return result


def empty_record():
    arrays = ['files', 'folder_paths', 'folders', 'rq_categories', 'keywords_assigned',
              'authors', 'author_objects', 'author_surnames', 'authors_display', 'isbn',
              'references_doi', 'references_openalex', 'keywords', 'methods', 'materials',
              'extractable_data', 'fid_reference_numbers', 'fid_contexts', 'component_dois']
    record = {key: [] for key in arrays}
    record.update(group='Unclassified', kind='', material='', tech='', rq='',
                  m2='Not assessed', notes='', journal='', journal_group='', abstract='',
                  availability='Not downloaded — BibTeX import', citation_count=None,
                  openalex_id=None, local_citations=0, doi=None, year=None,
                  classification_basis='BibTeX metadata only; content classification not assessed.')
    return record


def from_bib(entry):
    record = empty_record()
    typ = entry['ENTRYTYPE'].lower()
    record.update(title=text(entry.get('title')), bibtex_key=entry['ID'],
                  bibtex_keys=[entry['ID']], bibtex_fields=entry,
                  metadata_source='BibTeX import', document_subtype=typ)
    record['document_type'] = ({'book': 'Book', 'inbook': 'Book', 'incollection': 'Book',
        'phdthesis': 'Dissertation', 'mastersthesis': 'Dissertation', 'thesis': 'Dissertation',
        'inproceedings': 'Conference paper', 'proceedings': 'Book',
        'manual': 'Industrial / standards / protocols', 'techreport': 'Report',
        'article': 'Paper'}).get(typ, 'Other')
    record['kind'] = record['document_type']
    record['doi'] = doi(entry.get('doi')) or doi(entry.get('url'))
    year = re.search(r'\b\d{4}\b', entry.get('year', entry.get('date', '')))
    record['year'] = int(year.group()) if year else None
    for target, source in [('journal', 'journal'), ('publisher', 'publisher'),
                           ('volume', 'volume'), ('issue', 'number'), ('page', 'pages'),
                           ('abstract', 'abstract'), ('book_title', 'booktitle')]:
        record[target] = text(entry.get(source))
    record['url'] = entry.get('url') or ('https://doi.org/' + record['doi'] if record['doi'] else '')
    record['isbn'] = [re.sub(r'[^0-9Xx]', '', v).upper()
                      for v in re.split(r'[;,]', entry.get('isbn', '')) if v.strip()]
    record['author_objects'] = authors(entry.get('author') or entry.get('editor', ''))
    if not entry.get('author') and entry.get('editor'): record['creator_role'] = 'Editors'
    record['authors'] = [' '.join(filter(None, [a['given'], a['family']])) for a in record['author_objects']]
    record['authors_display'] = record['authors'][:]
    record['author_surnames'] = sorted({a['family'] for a in record['author_objects']})
    record['keywords_bibtex'] = [text(v) for v in re.split(r'[;,]', entry.get('keywords', '')) if v.strip()]
    record['journal_group'] = record['journal']
    for prefix in ['Physical Review', 'Journal of Physical Chemistry', 'Journal of Polymer Science']:
        if record['journal'].startswith(prefix): record['journal_group'] = prefix
    record['doi_status'] = 'Imported DOI — not verified' if record['doi'] else 'No DOI supplied'
    # Keep attachment fields verbatim. A BibTeX path does not prove a PDF exists.
    record['bibtex_file_field'] = entry.get('file', '')
    record['primary_identifier'] = ('ISBN: ' + ', '.join(record['isbn'])
        if record['document_type'] == 'Book' and record['isbn'] else
        'DOI: ' + record['doi'] if record['doi'] else '')
    identity = record['doi'] or '|'.join([record['title'].casefold(), str(record['year']),
                                         ';'.join(record['authors']), entry['ID']])
    record['id'] = 'bib' + hashlib.sha256(identity.encode()).hexdigest()[:16]
    return record


def match_record(candidate, papers):
    if candidate['doi']:
        matches = [p for p in papers if doi(p.get('doi')) == candidate['doi']]
        if len(matches) == 1: return matches[0]
    # Do not merge chapters just because they share their parent book's ISBN.
    title = candidate['title'].casefold()
    matches = [p for p in papers if title and p.get('title', '').casefold() == title
               and p.get('year') == candidate['year']
               and p.get('author_surnames') == candidate['author_surnames']
               and not (p.get('doi') and candidate['doi'] and doi(p['doi']) != candidate['doi'])]
    return matches[0] if len(matches) == 1 else None


def fetch_work(record, api_key):
    identifier = (record.get('openalex_id') or '').rstrip('/').split('/')[-1]
    if not re.fullmatch(r'W\d+', identifier):
        identifier = 'https://doi.org/' + record['doi'] if record.get('doi') else None
    if not identifier: return None
    url = 'https://api.openalex.org/works/' + urllib.parse.quote(identifier, safe='')
    headers = {'User-Agent': 'LiteratureAtlasBibImporter/1.0'}
    if api_key: headers['Authorization'] = 'Bearer ' + api_key
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404: return None
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f'OpenAlex HTTP {error.code}') from None
            time.sleep(2 ** attempt)
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError('OpenAlex connection failed or timed out') from None


def enrich(record, work):
    record['openalex_id'] = work['id']
    record['citation_count'] = work.get('cited_by_count')
    record['citation_count_source'] = 'OpenAlex'
    record['citation_count_date'] = dt.date.today().isoformat()
    record['references_openalex'] = work.get('referenced_works', [])
    record['metadata_openalex_updated_at'] = work.get('updated_date')
    # Fill empty bibliographic fields, never replace manually corrected titles.
    if not record.get('title'): record['title'] = work.get('title') or ''
    if not record.get('year'): record['year'] = work.get('publication_year')
    if not record.get('abstract') and work.get('abstract_inverted_index'):
        positions = [(i, word) for word, indexes in work['abstract_inverted_index'].items() for i in indexes]
        record['abstract'] = ' '.join(word for _, word in sorted(positions))


def rebuild_edges(data):
    papers = data['papers']
    ids = {p['id'] for p in papers}
    by_doi = {doi(p.get('doi')): p['id'] for p in papers if doi(p.get('doi'))}
    by_oa = {p['openalex_id'].split('/')[-1]: p['id'] for p in papers if p.get('openalex_id')}
    edges = {}
    def add(source, target, evidence):
        if source not in ids or target not in ids or source == target: return
        edge = edges.setdefault((source, target), {'source': source, 'target': target, 'sources': []})
        if evidence not in edge['sources']: edge['sources'].append(evidence)
    # Preserve existing evidence, including curated book-component links.
    for edge in data.get('edges', []):
        for evidence in edge.get('sources') or ['Existing atlas link']:
            add(edge['source'], edge['target'], evidence)
    for paper in papers:
        for ref in paper.get('references_doi', []):
            add(paper['id'], by_doi.get(doi(ref)), 'Reference DOI')
        for ref in paper.get('references_openalex', []):
            add(paper['id'], by_oa.get(ref.split('/')[-1]), 'OpenAlex referenced_works')
    data['edges'] = list(edges.values())
    counts = dict.fromkeys(ids, 0)
    for edge in data['edges']: counts[edge['target']] += 1
    for paper in papers: paper['local_citations'] = counts[paper['id']]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bib', type=Path)
    parser.add_argument('--existing', type=Path)
    parser.add_argument('--output', type=Path, default=Path('library_updated.json'))
    parser.add_argument('--online', action='store_true', help='Refresh imported records through OpenAlex')
    parser.add_argument('--refresh-all', action='store_true', help='With --online, refresh every record')
    parser.add_argument('--overwrite', action='store_true', help='Allow replacing an existing output file')
    args = parser.parse_args()

    if args.refresh_all and not args.online: parser.error('--refresh-all requires --online')
    if args.output.exists() and not args.overwrite: parser.error('Output exists; use another filename or --overwrite')
    if args.output.resolve() == args.bib.resolve(): parser.error('Output cannot replace the BibTeX input')
    data = json.loads(args.existing.read_text(encoding='utf-8-sig')) if args.existing else {
        'schema_version': '2.0', 'rq_definitions': RQ, 'papers': [], 'edges': [],
        'citation_direction': 'citing → cited', 'file_locations': [], 'fid_references': [],
        'missing_folder_files': [], 'notes': []}

    if not isinstance(data.get('papers'), list): parser.error('Existing JSON must contain a papers array')
    if len({p['id'] for p in data['papers']}) != len(data['papers']): parser.error('Existing JSON contains duplicate IDs')
    bib_parser = BibTexParser(common_strings=True)
    bib_parser.ignore_nonstandard_types = False
    bib_parser.add_missing_from_crossref = True
    database = bibtexparser.loads(args.bib.read_text(encoding='utf-8-sig'), parser=bib_parser)
    if not database.entries: parser.error('No BibTeX entries found; no output written')
    touched, added, merged = set(), 0, 0

    for entry in database.entries:
        candidate = from_bib(entry)
        old = match_record(candidate, data['papers'])
        if old:
            merged += 1
            for key, value in candidate.items():
                if key not in MANUAL and key != 'id' and old.get(key) in (None, '', []):
                    old[key] = copy.deepcopy(value)
            old.setdefault('bibtex_keys', [])
            if entry['ID'] not in old['bibtex_keys']: old['bibtex_keys'].append(entry['ID'])
            touched.add(old['id'])
        else:
            # Identical keys from distinct entries must never create duplicate IDs.
            used = {p['id'] for p in data['papers']}
            while candidate['id'] in used: candidate['id'] += '_2'
            data['papers'].append(candidate)
            touched.add(candidate['id'])
            added += 1
    failures = []

    if args.online:
        records = data['papers'] if args.refresh_all else [p for p in data['papers'] if p['id'] in touched]
        for i, record in enumerate(records, 1):
            print(f'OpenAlex {i}/{len(records)}: {record["id"]}', file=sys.stderr)
            try:
                work = fetch_work(record, os.getenv('OPENALEX_API_KEY', ''))
                if work: enrich(record, work)
            except (RuntimeError, ValueError, KeyError) as error:
                failures.append({'id': record['id'], 'error': str(error)})
            time.sleep(0.12)
    rebuild_edges(data)
    data['generated_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    data['last_import'] = {'source': args.bib.name, 'added': added, 'matched': merged,
                           'online': args.online, 'failures': failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(args.output)
    print(f'Saved {args.output}: {len(data["papers"])} records, {len(data["edges"])} links; '
          f'{added} new, {merged} matched, {len(failures)} online failures.')
    if failures: print('Existing values retained on lookup failures; see last_import.failures.', file=sys.stderr)


if __name__ == '__main__':
    main()
