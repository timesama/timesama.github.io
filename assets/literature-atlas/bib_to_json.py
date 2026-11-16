#!/usr/bin/env python3
"""Import BibTeX or migrate a legacy atlas to compact JSON (schema 3.0).
Python 3.10+. Offline by default; --online enables OpenAlex lookups.
"""
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
CATEGORY_NAMES = ('method', 'material', 'data', 'folder', 'keyword', 'general', 'research_question')

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


def unique(values):
    return list(dict.fromkeys(value for value in values if value))


def as_list(value):
    return value if isinstance(value, list) else [value] if value else []


def new_record(entry):
    """Keep all BibTeX fields, including unfamiliar/custom fields, once."""
    identity = doi(entry.get('doi')) or json.dumps(entry, sort_keys=True, ensure_ascii=False)
    return {
        'id': 'bib' + hashlib.sha256(identity.encode()).hexdigest()[:16],
        'bib': copy.deepcopy(entry),
        'citations': {'total': None, 'source': None, 'updated': None, 'openalex_id': None},
        'files': [],
        'categories': {name: [] for name in CATEGORY_NAMES}
    }


def migrate_record(old):
    if 'bib' in old:
        record = copy.deepcopy(old)
        for name in CATEGORY_NAMES:
            record.setdefault('categories', {}).setdefault(name, [])
        record.setdefault('files', [])
        record.setdefault('citations', {})
        return record

    bib = copy.deepcopy(old.get('bibtex_fields') or {})
    types = {'Paper': 'article', 'Review': 'article', 'Correction': 'article',
             'Book': 'book', 'Dissertation': 'phdthesis', 'Conference paper': 'inproceedings',
             'Manuscript': 'unpublished'}
    bib['ENTRYTYPE'] = bib.get('ENTRYTYPE') or types.get(old.get('document_type'), 'misc')
    bib['ID'] = old.get('bibtex_key') or bib.get('ID') or old['id']
    # The top-level legacy values may contain manual corrections newer than raw BibTeX.
    mapping = {'title': 'title', 'year': 'year', 'journal': 'journal', 'volume': 'volume',
               'issue': 'number', 'page': 'pages', 'publisher': 'publisher', 'edition': 'edition',
               'doi': 'doi', 'url': 'url', 'abstract': 'abstract', 'language': 'language',
               'book_title': 'booktitle', 'school': 'school', 'institution': 'institution'}
    for source, target in mapping.items():
        if old.get(source) not in (None, '', []):
            bib[target] = str(old[source])
    if old.get('isbn'): bib['isbn'] = '; '.join(as_list(old['isbn']))
    # Display names preserve manual translations and the supplied author order.
    names = old.get('authors_display') or old.get('authors')
    if names:
        bib['editor' if old.get('creator_role') == 'Editors' else 'author'] = ' and '.join(names)
    if old.get('keywords_bibtex') and not bib.get('keywords'):
        bib['keywords'] = '; '.join(old['keywords_bibtex'])
    record = new_record(bib)
    record['id'] = old['id']
    record['citations'] = {
        'total': old.get('citation_count'), 'source': old.get('citation_count_source'),
        'updated': old.get('citation_count_date'), 'openalex_id': old.get('openalex_id')}
    paths = as_list(old.get('folder_paths'))
    filenames_in_paths = {path.replace('\\', '/').split('/')[-1] for path in paths}
    record['files'] = unique(paths + [name for name in old.get('files', []) if name not in filenames_in_paths])
    mapping = {'method': 'methods', 'material': 'materials', 'data': 'extractable_data',
               'folder': 'folders', 'keyword': 'keywords', 'general': 'group',
               'research_question': 'rq_categories'}
    record['categories'] = {key: as_list(old.get(value)) for key, value in mapping.items()}
    if old.get('notes'): record['notes'] = old['notes']
    return record


def normalized_title(record):
    return text(record['bib'].get('title')).casefold()


def find_match(candidate, papers):
    candidate_doi = doi(candidate['bib'].get('doi')) or doi(candidate['bib'].get('url'))
    matches = [p for p in papers if candidate_doi and
               (doi(p['bib'].get('doi')) or doi(p['bib'].get('url'))) == candidate_doi]
    if len(matches) == 1: return matches[0]
    # Exact title/year/authors fallback; never merge different known DOIs.
    matches = []
    for paper in papers:
        other_doi = doi(paper['bib'].get('doi')) or doi(paper['bib'].get('url'))
        if candidate_doi and other_doi and candidate_doi != other_doi: continue
        if not normalized_title(candidate): continue
        if normalized_title(candidate) != normalized_title(paper): continue
        if candidate['bib'].get('year') != paper['bib'].get('year'): continue
        if text(candidate['bib'].get('author')).casefold() != text(paper['bib'].get('author')).casefold(): continue
        matches.append(paper)
    return matches[0] if len(matches) == 1 else None


def add_references(papers, edges, references):
    by_doi = {doi(p['bib'].get('doi')): p['id'] for p in papers if doi(p['bib'].get('doi'))}
    by_oa = {p['citations']['openalex_id'].split('/')[-1]: p['id'] for p in papers
             if p['citations'].get('openalex_id')}
    for source, refs in references.items():
        for value in refs.get('doi', []):
            if doi(value) in by_doi: edges.add((source, by_doi[doi(value)]))
        for value in refs.get('openalex', []):
            if value.split('/')[-1] in by_oa: edges.add((source, by_oa[value.split('/')[-1]]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bib', nargs='?', type=Path, help='Optional when migrating --existing JSON only')
    parser.add_argument('--existing', type=Path)
    parser.add_argument('--output', type=Path, default=Path('library_compact.json'))
    parser.add_argument('--online', action='store_true')
    parser.add_argument('--refresh-all', action='store_true')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if not args.bib and not args.existing: parser.error('Supply a .bib file or --existing JSON')
    if args.refresh_all and not args.online: parser.error('--refresh-all requires --online')
    if args.output.exists() and not args.overwrite: parser.error('Output exists; choose a new filename or use --overwrite')
    if args.bib and args.output.resolve() == args.bib.resolve(): parser.error('Output cannot replace BibTeX input')
    old = json.loads(args.existing.read_text(encoding='utf-8-sig')) if args.existing else {'papers': [], 'edges': []}
    if not isinstance(old.get('papers'), list): parser.error('Existing JSON needs a papers array')
    papers = [migrate_record(p) for p in old['papers']]
    if len({p['id'] for p in papers}) != len(papers): parser.error('Duplicate existing paper IDs')
    edges = {(e['source'], e['target']) for e in old.get('edges', [])}
    refs = {p['id']: {'doi': p.get('references_doi', []), 'openalex': p.get('references_openalex', [])}
            for p in old['papers']}
    touched = set()
    added = matched = 0
    if args.bib:
        bib_parser = BibTexParser(common_strings=True)
        bib_parser.ignore_nonstandard_types = False
        bib_parser.add_missing_from_crossref = True
        entries = bibtexparser.loads(args.bib.read_text(encoding='utf-8-sig'), parser=bib_parser).entries
        if not entries: parser.error('No BibTeX entries found; no output written')
        for entry in entries:
            candidate = new_record(entry)
            record = find_match(candidate, papers)
            if record:
                matched += 1
                for key, value in entry.items():
                    if record['bib'].get(key) in (None, ''): record['bib'][key] = value
            else:
                record = candidate
                used = {p['id'] for p in papers}
                while record['id'] in used: record['id'] += '_2'
                papers.append(record)
                added += 1
            touched.add(record['id'])
    failures = []
    if args.online:
        selected = papers if args.refresh_all or not args.bib else [p for p in papers if p['id'] in touched]
        for i, record in enumerate(selected, 1):
            print(f'OpenAlex {i}/{len(selected)}: {record["id"]}', file=sys.stderr)
            query = {'openalex_id': record['citations'].get('openalex_id'),
                     'doi': doi(record['bib'].get('doi')) or doi(record['bib'].get('url'))}
            try:
                work = fetch_work(query, os.getenv('OPENALEX_API_KEY', ''))
                if work:
                    record['citations'] = {'total': work.get('cited_by_count'), 'source': 'OpenAlex',
                        'updated': dt.date.today().isoformat(), 'openalex_id': work['id']}
                    refs.setdefault(record['id'], {})['openalex'] = work.get('referenced_works', [])
                    for field, value in [('title', work.get('title')), ('year', work.get('publication_year'))]:
                        if value and not record['bib'].get(field): record['bib'][field] = str(value)
                    inverted = work.get('abstract_inverted_index')
                    if inverted and not record['bib'].get('abstract'):
                        positions = [(i, word) for word, indexes in inverted.items() for i in indexes]
                        record['bib']['abstract'] = ' '.join(word for _, word in sorted(positions))
            except (RuntimeError, ValueError, KeyError) as error:
                failures.append({'id': record['id'], 'error': str(error)})
            time.sleep(0.12)
    add_references(papers, edges, refs)
    ids = {p['id'] for p in papers}
    result = {'schema_version': '3.0', 'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'papers': papers, 'edges': [{'source': a, 'target': b} for a, b in sorted(edges)
                                         if a in ids and b in ids and a != b]}
    if old.get('rq_definitions'): result['rq_definitions'] = old['rq_definitions']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_name(args.output.name + '.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(args.output)
    print(f'Saved {args.output}: {len(papers)} records, {len(result["edges"])} links; {added} new, {matched} matched.')
    for failure in failures: print(f'Lookup failed for {failure["id"]}: {failure["error"]}', file=sys.stderr)
    if failures: print('Previous values retained for failed lookups.', file=sys.stderr)


if __name__ == '__main__':
    main()
