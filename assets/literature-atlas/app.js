'use strict';
const $ = s => document.querySelector(s),
    NS = 'http://www.w3.org/2000/svg';
let data, visible = [],
    edges = [],
    selected = null,
    nodes = [],
    view = {
        x: 0,
        y: 0,
        k: 1
    },
    drag = null,
    hover = null,
    minYear = 1900,
    maxYear = 2026;
const facets = [
    ['rq_categories', 'Research question'],
    ['group', 'General category'],
    ['methods', 'Method'],
    ['materials', 'Material'],
    ['extractable_data', 'Data / quantities'],
    ['folders', 'Folder topic'],
    ['keywords', 'Keyword'],
    ['document_type', 'Document type'],
    ['author_surnames', 'Author surname'],
    ['journal_group', 'Journal family'],
    ['availability', 'PDF availability']
];
const arr = x => Array.isArray(x) ? x : x ? [x] : [];

function el(tag, text, cls) {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (cls) e.className = cls;
    return e
}

function option(v, text = v) {
    const o = el('option', text);
    o.value = v;
    return o
}

function init(d) {
    if (!d || !Array.isArray(d.papers) || !Array.isArray(d.edges)) throw Error(
        'Expected papers and edges arrays');
    data = d;
    selected = null;
    $('#facets').replaceChildren();
    for (const [key, label] of facets) {
        const l = el('label', label),
            s = el('select');
        s.id = key;
        s.append(option('', 'All'));
        l.append(s);
        $('#facets').append(l);
        s.onchange = filter
    }
    const ys = data.papers.map(p => p.year).filter(Number.isFinite);
    minYear = Math.min(...ys);
    maxYear = Math.max(...ys);
    $('#yearLegend').textContent = `Publication year  ${minYear} — ${maxYear}`;
    $('#status').textContent =
        `Snapshot ${d.generated_at?.slice(0,10)||'undated'} · Dropdown counts respect the other filters. Citation links depend on source coverage.`;
    filter()
}

function filter() {
    if (!data) return;
    const q = $('#search').value.toLowerCase(),
        lo = Number($('#from').value) || -Infinity,
        hi = Number($('#to').value) || Infinity;
    const picked = Object.fromEntries(facets.map(([k]) => [k, $('#' + k).value]));
    const base = data.papers.filter(p => (!q || [p.title, p.doi, ...arr(p.isbn), ...arr(p.authors),
        ...arr(p.author_surnames), ...arr(p.methods), ...arr(p.keywords), ...arr(p
            .folder_paths)
    ].join(' ').toLowerCase().includes(q)) && ((p.year == null && lo === -Infinity && hi ===
        Infinity) || (p.year != null && p.year >= lo && p.year <= hi)));
    const matches = (p, except = '') => facets.every(([k]) => k === except || !picked[k] || arr(p[
        k]).includes(picked[k]));
    visible = base.filter(p => matches(p));
    for (const [key] of facets) {
        const eligible = base.filter(p => matches(p, key)),
            counts = new Map();
        for (const p of eligible)
            for (const v of new Set(arr(p[key]))) counts.set(v, (counts.get(v) || 0) + 1);
        const vals = [...new Set(data.papers.flatMap(p => arr(p[key])))].sort((a, b) => (counts.get(
            b) || 0) - (counts.get(a) || 0) || a.localeCompare(b));
        const select = $('#' + key);
        select.replaceChildren(option('', `All (${eligible.length})`));
        for (const v of vals) {
            const label = key === 'rq_categories' ? `${v} — ${data.rq_definitions[v]||''}` : v;
            select.append(option(v, `${label} (${counts.get(v)||0})`))
        }
        select.value = picked[key] || ''
    }
    const ids = new Set(visible.map(p => p.id));
    edges = data.edges.filter(e => ids.has(e.source) && ids.has(e.target));
    if (selected && !ids.has(selected.id)) selected = null;
    $('#count').textContent = `${visible.length} of ${data.papers.length} records`;
    $('#coverage').textContent =
        `${edges.length} citation links · ${visible.filter(p=>p.citation_count!=null).length} with global citation counts`;
    $('#empty').hidden = visible.length > 0;
    layout();
    renderList();
    if (!selected) blankDetails()
}

function radius(p) {
    const metric = $('#size').value;
    const count = p[metric];
    const minimumRadius = 7;
    const maximumRadius = minimumRadius * 10;

    // Unknown counts remain small; they are not treated as zero citations.
    if (!Number.isFinite(count)) return minimumRadius;

    const counts = visible
        .map(paper => paper[metric])
        .filter(Number.isFinite);
    const minimumCount = Math.min(...counts);
    const maximumCount = Math.max(...counts);

    // Equal counts (including a single visible paper) get equal, small bubbles.
    if (maximumCount === minimumCount) return minimumRadius;

    const fraction = (count - minimumCount) / (maximumCount - minimumCount);
    return minimumRadius + fraction * (maximumRadius - minimumRadius);
}

let layoutFrame = null;

// Separate circles without changing their citation-based radii.
function separateBubbles(items) {
    let largestOverlap = 0;
    for (let i = 0; i < items.length; i++) {
        for (let j = i + 1; j < items.length; j++) {
            const a = items[i];
            const b = items[j];
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let distance = Math.hypot(dx, dy);
            if (distance < 0.000001) {
                dx = 1;
                dy = 0;
                distance = 1;
            }
            const overlap = a.r + b.r + 7 - distance;
            if (overlap <= 0) continue;
            largestOverlap = Math.max(largestOverlap, overlap);
            const shift = overlap / 2;
            a.x -= dx / distance * shift;
            a.y -= dy / distance * shift;
            b.x += dx / distance * shift;
            b.y += dy / distance * shift;
        }
    }
    return largestOverlap;
}

function layout() {
    // Restart from the currently displayed positions if controls change rapidly.
    if (layoutFrame !== null) cancelAnimationFrame(layoutFrame);
    layoutFrame = null;
    const previous = new Map(nodes.map(node => [node.p.id, { ...node }]));
    const groups = [...new Set(visible.map(paper => paper.group))];
    const targets = visible.map((paper, i) => {
        const old = previous.get(paper.id);
        const angle = groups.indexOf(paper.group) / groups.length * Math.PI * 2;
        const phi = i * 2.39996;
        const distance = 18 * Math.sqrt(i % 25);
        return {
            p: paper,
            x: old ? old.x : Math.cos(angle) * 200 + Math.cos(phi) * distance,
            y: old ? old.y : Math.sin(angle) * 200 + Math.sin(phi) * distance,
            r: radius(paper)
        };
    });
    const index = new Map(targets.map(node => [node.p.id, node]));
    for (let iteration = 0; iteration < 150; iteration++) {
        for (const edge of edges) {
            const a = index.get(edge.source);
            const b = index.get(edge.target);
            if (!a || !b) continue;
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            if (Math.hypot(dx, dy) > 110) {
                a.x += dx * 0.0008;
                b.x -= dx * 0.0008;
                a.y += dy * 0.0008;
                b.y -= dy * 0.0008;
            }
        }
        separateBubbles(targets);
    }
    // Finish with collision resolution only: citation attraction must not
    // pull the circles back into each other on the final iteration.
    for (let iteration = 0; iteration < 600; iteration++) {
        if (separateBubbles(targets) < 0.01) break;
    }

    if (!previous.size || !targets.length ||
        window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        nodes = targets;
        fit();
        return;
    }

    const starts = targets.map(target => previous.get(target.p.id) || {
        ...target,
        r: 0
    });
    nodes = targets.map((target, i) => ({ ...target, ...starts[i], p: target.p }));
    const startedAt = performance.now();
    const duration = 650;

    function animate(now) {
        const progress = Math.min(1, (now - startedAt) / duration);
        const eased = progress * progress * (3 - 2 * progress);
        nodes.forEach((node, i) => {
            const start = starts[i];
            const target = targets[i];
            node.x = start.x + (target.x - start.x) * eased;
            node.y = start.y + (target.y - start.y) * eased;
            node.r = start.r + (target.r - start.r) * eased;
        });
        for (let iteration = 0; iteration < 20; iteration++) {
            if (separateBubbles(nodes) < 0.01) break;
        }
        if (progress < 1) {
            fit();
            layoutFrame = requestAnimationFrame(animate);
        } else {
            nodes = targets;
            layoutFrame = null;
            fit();
        }
    }
    layoutFrame = requestAnimationFrame(animate);
}
const cv = $('#canvas'),
    ctx = cv.getContext('2d');

function resize() {
    const r = cv.getBoundingClientRect(),
        dpr = devicePixelRatio || 1;
    cv.width = r.width * dpr;
    cv.height = r.height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw()
}

function fit() {
    const r = cv.getBoundingClientRect();
    if (!nodes.length) {
        draw();
        return
    }
    const a = Math.min(...nodes.map(n => n.x - n.r)),
        b = Math.max(...nodes.map(n => n.x + n.r)),
        c = Math.min(...nodes.map(n => n.y - n.r)),
        d = Math.max(...nodes.map(n => n.y + n.r));
    view.k = Math.min((r.width - 60) / (b - a || 1), (r.height - 150) / (d - c || 1), 2);
    view.x = r.width / 2 - (a + b) / 2 * view.k;
    view.y = (r.height - 80) / 2 - (c + d) / 2 * view.k;
    resize()
}

function color(p) {
    return p.year == null ? '#a4acb8' :
        `hsl(${215-(p.year-minYear)/Math.max(1,maxYear-minYear)*210} 55% 55%)`
}

function draw() {
    const r = cv.getBoundingClientRect();
    ctx.clearRect(0, 0, r.width, r.height);
    ctx.save();
    ctx.translate(view.x, view.y);
    ctx.scale(view.k, view.k);
    const by = new Map(nodes.map(n => [n.p.id, n]));
    const mode = $('#arrows').value;
    for (const e of edges) {
        if (mode === 'none' || (mode === 'focus' && (!selected || (e.source !== selected.id && e
                .target !== selected.id)))) continue;
        const a = by.get(e.source),
            b = by.get(e.target),
            dx = b.x - a.x,
            dy = b.y - a.y,
            l = Math.hypot(dx, dy) || 1;
        if (l < a.r + b.r) continue;
        const ux = dx / l,
            uy = dy / l,
            tx = b.x - ux * (b.r + 3),
            ty = b.y - uy * (b.r + 3);
        ctx.strokeStyle = selected && (e.source === selected.id || e.target === selected.id) ?
            '#52667fc0' : '#9eabb64f';
        ctx.lineWidth = 1 / view.k;
        ctx.beginPath();
        ctx.moveTo(a.x + ux * a.r, a.y + uy * a.r);
        ctx.lineTo(tx, ty);
        ctx.stroke();
        ctx.fillStyle = ctx.strokeStyle;
        ctx.beginPath();
        ctx.moveTo(tx, ty);
        ctx.lineTo(tx - ux * 7 - uy * 3, ty - uy * 7 + ux * 3);
        ctx.lineTo(tx - ux * 7 + uy * 3, ty - uy * 7 - ux * 3);
        ctx.fill()
    }
    for (const n of nodes) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = color(n.p);
        ctx.globalAlpha = selected && selected.id !== n.p.id ? .62 : .88;
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.strokeStyle = selected?.id === n.p.id ? '#152f50' : '#ffffff';
        ctx.lineWidth = (selected?.id === n.p.id ? 3 : 1) / view.k;
        ctx.setLineDash(n.p[$('#size').value] == null ? [3 / view.k, 2 / view.k] : []);
        ctx.stroke();
        ctx.setLineDash([]);
        if (selected?.id === n.p.id || n.r * view.k > 18) {
            ctx.font = `${10/view.k}px Arial`;
            ctx.textAlign = 'center';
            ctx.fillStyle = '#233347';
            const label = (n.p.author_surnames?.[0] || n.p.title.split(' ')[0]) + ' ' + (n.p.year ||
                '');
            ctx.fillText(label, n.x, n.y + n.r + 12 / view.k)
        }
    }
    ctx.restore()
}

function hit(e) {
    const r = cv.getBoundingClientRect(),
        x = (e.clientX - r.left - view.x) / view.k,
        y = (e.clientY - r.top - view.y) / view.k;
    return [...nodes].reverse().find(n => Math.hypot(n.x - x, n.y - y) < n.r + 3 / view.k)
}
cv.onpointerdown = e => {
    drag = {
        x: e.clientX,
        y: e.clientY,
        ox: view.x,
        oy: view.y,
        moved: false
    };
    cv.setPointerCapture(e.pointerId)
};
cv.onpointermove = e => {
    if (drag) {
        const dx = e.clientX - drag.x,
            dy = e.clientY - drag.y;
        drag.moved ||= Math.hypot(dx, dy) > 4;
        view.x = drag.ox + dx;
        view.y = drag.oy + dy;
        draw();
        return
    }
    const n = hit(e),
        tip = $('#tooltip');
    tip.hidden = !n;
    if (n) {
        tip.textContent = n.p.title;
        const r = cv.getBoundingClientRect();
        tip.style.left = Math.max(0, Math.min(e.clientX - r.left + 12, r.width - 290)) + 'px';
        tip.style.top = Math.max(0, e.clientY - r.top - 65) + 'px'
    }
};
cv.onpointerup = e => {
    if (drag && !drag.moved) {
        const n = hit(e);
        if (n) select(n.p)
    }
    drag = null
};
cv.onpointercancel = () => drag = null;
cv.onpointerleave = () => $('#tooltip').hidden = true;
cv.addEventListener('wheel', e => {
    e.preventDefault();
    const r = cv.getBoundingClientRect();
    zoom(Math.exp(-e.deltaY * .001), e.clientX - r.left, e.clientY - r.top)
}, {
    passive: false
});

function zoom(k, x = cv.clientWidth / 2, y = cv.clientHeight / 2) {
    const old = view.k;
    view.k = Math.max(.15, Math.min(8, view.k * k));
    view.x = x - (x - view.x) * view.k / old;
    view.y = y - (y - view.y) * view.k / old;
    draw()
}

function blankDetails() {
    const d = $('#details');
    d.replaceChildren(el('div', 'PAPER DETAILS', 'eyebrow'), el('h2', 'Select a bubble'), el('p',
        'Inspect its bibliography, source folders and citation connections.'), el('p',
        'Only metadata is loaded. PDFs stay on your computer.', 'hint'))
}

function select(p) {
    selected = p;
    const d = $('#details');
    d.replaceChildren(el('div', `${p.document_type} · ${p.year??'Year unknown'}`, 'eyebrow'), el(
        'h2', p.title), el('p', (p.author_surnames || []).join(', ') ||
        'Author metadata unresolved'), el('p', p.journal || p.publisher || '', 'muted'));
    if (p.isbn?.length) d.append(el('p', 'ISBN: ' + p.isbn.join(', ')));
    if (p.book_title) d.append(el('p', 'In: ' + p.book_title));
    if (p.doi) {
        const a = el('a', p.doi);
        a.href = 'https://doi.org/' + encodeURI(p.doi);
        a.target = '_blank';
        a.rel = 'noopener';
        d.append(a)
    }
    d.append(el('div', p.citation_count == null ? 'Unknown' : p.citation_count.toLocaleString(),
        'stat'), el('p',
        `OpenAlex citations${p.citation_count_date?' · '+p.citation_count_date:''}`, 'muted'
        ));
    for (const [name, values, key] of [
            ['Research questions', p.rq_categories, 'rq_categories'],
            ['General category', [p.group], 'group'],
            ['Methods', p.methods, 'methods'],
            ['Materials', p.materials, 'materials'],
            ['Data / quantities', p.extractable_data, 'extractable_data'],
            ['Keywords', p.keywords, 'keywords']
        ]) {
        d.append(el('h3', name));
        for (const v of [...arr(values)].sort((a, b) => data.papers.filter(x => arr(x[key])
                    .includes(b)).length - data.papers.filter(x => arr(x[key]).includes(a))
                .length || a.localeCompare(b))) {
            const count = data.papers.filter(x => arr(x[key]).includes(v)).length;
            const b = el('button', `${v} (${count})`, 'chip');
            b.title = 'Collection-wide count';
            b.onclick = () => {
                $('#' + key).value = v;
                filter()
            };
            d.append(b)
        }
    }
    d.append(el('p',
        'Quantity tags indicate what is discussed or potentially extractable; they do not certify a complete numerical extraction.',
        'hint'), el('h3', 'Second-moment role'), el('p', p.m2 || 'Not assessed'), el('h3',
        'Source locations'));
    for (const path of p.folder_paths) d.append(el('div', path, 'path'));
    if (!p.folder_paths.length) d.append(el('p', p.availability === 'Downloaded' ?
        'Uploaded; folder path not matched' : p.availability, 'hint'));
    const f = el('details'),
        summary = el('summary', `${p.files.length} uploaded file(s)`);
    f.append(summary);
    for (const n of p.files) f.append(el('div', n, 'path'));
    d.append(f);
    if (p.fid_reference_numbers?.length) d.append(el('h3', 'FID manuscript'), el('p',
        'References ' + p.fid_reference_numbers.join(', ')), el('p', (p.fid_contexts || [])
        .slice(0, 3).join('\n'), 'hint'));
    if (p.component_titles?.length) {
        d.append(el('h3', `Included chapters (${p.component_titles.length})`));
        const components = el('details');
        components.append(el('summary', 'Show chapter titles'));
        for (const t of p.component_titles) components.append(el('p', t, 'hint'));
        d.append(components)
    }
    d.append(el('h3', 'Citation connections'));
    for (const dir of ['out', 'in']) {
        const ee = data.edges.filter(e => dir === 'out' ? e.source === p.id : e.target === p.id);
        d.append(el('p', `${dir==='out'?'Cites':'Cited by'} ${ee.length} collection records`));
        for (const e of ee) {
            const other = data.papers.find(x => x.id === (dir === 'out' ? e.target : e.source));
            const b = el('button', other.title, 'link');
            b.title = e.sources.join('; ');
            b.onclick = () => select(other);
            d.append(b)
        }
    }
    if (p.abstract) {
        const a = el('details');
        a.append(el('summary', 'Abstract'), el('p', p.abstract));
        d.append(a)
    }
    d.append(el('h3', 'Provenance and review'), el('p', p.doi_status, 'hint'), el('p', p.notes,
        'hint'));
    draw()
}

function renderList() {
    const list = $('#list');
    list.replaceChildren();
    const t = el('table'),
        head = el('tr');
    for (const s of ['Paper', 'Year', 'Citations', 'Type']) head.append(el('th', s));
    const th = el('thead');
    th.append(head);
    t.append(th);
    const body = el('tbody'),
        key = $('#sort').value === 'authors' ? 'author_surnames' : $('#sort').value;
    const sorted = [...visible].sort((a, b) => ['year', 'citation_count'].includes(key) ? (b[key] ??
        -1) - (a[key] ?? -1) : String(a[key] || '').localeCompare(String(b[key] || '')));
    for (const p of sorted) {
        const tr = el('tr'),
            td = el('td'),
            b = el('button', p.title);
        b.onclick = () => select(p);
        td.append(b, el('div', (p.author_surnames || []).join(', '), 'muted'));
        tr.append(td, el('td', p.year ?? '—'), el('td', p.citation_count ?? 'Unknown'), el('td', p
            .document_type));
        body.append(tr)
    }
    t.append(body);
    list.append(t)
}
for (const id of ['search', 'from', 'to']) $('#' + id).oninput = filter;
$('#sort').onchange = renderList;
$('#size').onchange = layout;
$('#arrows').onchange = draw;
$('#fit').onclick = fit;
$('#zoomIn').onclick = () => zoom(1.25);
$('#zoomOut').onclick = () => zoom(.8);
$('#reset').onclick = () => {
    for (const [k] of facets) $('#' + k).value = '';
    for (const k of ['search', 'from', 'to']) $('#' + k).value = '';
    filter()
};
$('#graphView').onclick = () => {
    $('#map').hidden = false;
    $('#list').hidden = true;
    $('#graphView').setAttribute('aria-pressed', 'true');
    $('#listView').setAttribute('aria-pressed', 'false');
    fit()
};
$('#listView').onclick = () => {
    $('#map').hidden = true;
    $('#list').hidden = false;
    $('#graphView').setAttribute('aria-pressed', 'false');
    $('#listView').setAttribute('aria-pressed', 'true')
};
$('#load').onclick = () => $('#file').click();
$('#file').onchange = async e => {
    try {
        init(JSON.parse(await e.target.files[0].text()))
    } catch (err) {
        $('#status').textContent = err.message
    }
};
$('#export').onclick = () => {
    const fields = ['title', 'author_surnames', 'year', 'journal', 'journal_group', 'doi',
        'isbn', 'group', 'rq_categories', 'methods', 'materials', 'extractable_data',
        'keywords', 'folder_paths', 'citation_count'
    ];
    const esc = v => '"' + String(Array.isArray(v) ? v.join('; ') : v ?? '').replaceAll('"',
        '""') + '"';
    const csv = [fields, ...visible.map(p => fields.map(k => p[k]))].map(r => r.map(esc).join(
        ',')).join('\r\n');
    const u = URL.createObjectURL(new Blob(['\uFEFF' + csv], {
            type: 'text/csv'
        })),
        a = el('a');
    a.href = u;
    a.download = 'selected_papers.csv';
    a.click();
    setTimeout(() => URL.revokeObjectURL(u), 1000)
};
new ResizeObserver(resize).observe($('#map'));
fetch('library.json').then(r => {
    if (!r.ok) throw Error('Metadata file not found');
    return r.json()
}).then(init).catch(() => {
    $('#count').textContent = 'Open your metadata file';
    $('#status').textContent =
        'Choose Open metadata and select library.json, or serve this folder with a local HTTP server.'
});
