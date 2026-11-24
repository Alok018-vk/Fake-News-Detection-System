const SAMPLES = {
  clickbait: `BREAKING: SHOCKING BOMBSHELL EXPOSED! You won't believe what government officials secretly admitted behind closed doors! The entire nation is stunned and furious after this mind-blowing revelation was leaked online! Share this immediately before authorities take it down! This is insane!`,
  
  reuters: `WASHINGTON (Reuters) - The U.S. Federal Reserve announced on Wednesday that it will maintain interest rates at their current target range, according to an official statement released following the Federal Open Market Committee meeting. Fed Chair Jerome Powell stated in a press briefing that economic indicators demonstrate steady expansion, while labor market conditions remain balanced. "Our policy stance is well-calibrated to assess ongoing financial data," Powell told reporters. Independent analysts noted that inflation figures published last week aligned with consensus forecasts.`,
  
  contradiction: `The Ministry of Health confirmed the new policy guidelines yesterday during a press conference. Officials declared that funding will increase significantly over the coming quarter to support local clinics. However, hours later, the department denied that any new budget was confirmed, stating that financial allocations will decrease sharply due to economic constraints. Representatives also argued that clinical trials were proved safe, while simultaneously publishing warnings that the treatments were disproved and dangerous.`
};

function loadSample(key) {
  const textarea = document.getElementById('news-input');
  if (SAMPLES[key]) {
    textarea.value = SAMPLES[key];
    updateCounts();
  }
}

function clearInput() {
  const textarea = document.getElementById('news-input');
  textarea.value = '';
  updateCounts();
  document.getElementById('audit-results').style.display = 'none';
}

function updateCounts() {
  const text = document.getElementById('news-input').value;
  const chars = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  document.getElementById('char-word-count').innerText = `CHARS: ${chars} | WORDS: ${words}`;
}

const inputElem = document.getElementById('news-input');
if (inputElem) {
  inputElem.addEventListener('input', updateCounts);
}

const apiKeyInput = document.getElementById('api-key-input');
if (apiKeyInput) {
  apiKeyInput.addEventListener('input', () => {
    const statusEl = document.getElementById('api-key-status');
    if (apiKeyInput.value.trim()) {
      statusEl.innerText = 'ACTIVE';
      statusEl.className = 'api-key-status active';
    } else {
      statusEl.innerText = 'NOT SET';
      statusEl.className = 'api-key-status';
    }
  });
}

async function executeAudit() {
  const text = document.getElementById('news-input').value.trim();
  const apiKey = (document.getElementById('api-key-input') || {}).value || '';
  const loading = document.getElementById('audit-loading');
  const resultsArea = document.getElementById('audit-results');
  const runBtn = document.getElementById('run-audit-btn');

  if (!text) {
    alert("INPUT ERROR: Please enter or paste some text first.");
    return;
  }

  loading.classList.add('active');
  runBtn.disabled = true;
  runBtn.innerText = apiKey.trim() ? "[ ANALYZING + AI FACT-CHECK... ]" : "[ ANALYZING... ]";

  try {
    const payload = { text };
    if (apiKey.trim()) payload.api_key = apiKey.trim();

    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis failed.");
    }

    const data = await res.json();
    renderAuditResults(data);
    resultsArea.style.display = 'block';
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    loadHistory();

  } catch (err) {
    alert("ERROR: " + err.message);
  } finally {
    loading.classList.remove('active');
    runBtn.disabled = false;
    runBtn.innerText = "[ ANALYZE CONTENT ]";
  }
}

function renderAuditResults(d) {
  const banner = document.getElementById('verdict-banner');
  const status = document.getElementById('verdict-status');
  const desc = document.getElementById('verdict-desc');
  const score = document.getElementById('verdict-score');

  banner.className = 'verdict-stamp';
  status.className = 'verdict-badge';

  const verdict = d.composite.verdict;
  if (verdict === 'REAL') {
    banner.classList.add('real');
    status.classList.add('real');
    status.innerText = `VERDICT: [ AUTHENTIC NEWS // REAL ]`;
  } else if (verdict === 'FAKE') {
    banner.classList.add('fake');
    status.classList.add('fake');
    status.innerText = `VERDICT: [ DECEPTIVE // FAKE NEWS ]`;
  } else {
    banner.classList.add('uncertain');
    status.classList.add('uncertain');
    status.innerText = `VERDICT: [ UNCERTAIN // VERIFY SOURCES ]`;
  }

  desc.innerText = d.composite.description;
  score.innerText = d.composite.score;

  document.getElementById('sensor-type').innerText = d.text_type.type.toUpperCase();
  document.getElementById('sensor-is-news').innerText = d.text_type.is_news ? 'YES' : 'NO';
  document.getElementById('sensor-reason').innerText = d.text_type.reason;

  document.getElementById('ml-model-name').innerText = d.ml_prediction.best_model.toUpperCase();
  document.getElementById('ml-real-pct').innerText = d.ml_prediction.real_probability + '%';
  document.getElementById('ml-real-bar').style.width = d.ml_prediction.real_probability + '%';
  document.getElementById('ml-fake-pct').innerText = d.ml_prediction.fake_probability + '%';
  document.getElementById('ml-fake-bar').style.width = d.ml_prediction.fake_probability + '%';

  document.getElementById('cred-clickbait').innerText = d.credibility.breakdown.clickbait_score + '/100';
  document.getElementById('cred-clickbait-bar').style.width = d.credibility.breakdown.clickbait_score + '%';

  document.getElementById('cred-source').innerText = d.credibility.breakdown.source_quality + '/100';
  document.getElementById('cred-source-bar').style.width = d.credibility.breakdown.source_quality + '%';

  document.getElementById('cred-tone').innerText = d.credibility.breakdown.emotional_tone + '/100';
  document.getElementById('cred-tone-bar').style.width = d.credibility.breakdown.emotional_tone + '%';

  document.getElementById('cred-struct').innerText = d.credibility.breakdown.structure_quality + '/100';
  document.getElementById('cred-struct-bar').style.width = d.credibility.breakdown.structure_quality + '%';

  document.getElementById('cred-verdict').innerText = d.credibility.verdict;

  document.getElementById('graph-keywords-count').innerText = d.graph_analysis.num_keywords;
  document.getElementById('graph-edges-count').innerText = d.graph_analysis.num_connections;
  document.getElementById('graph-components-count').innerText = d.graph_analysis.connected_components;
  document.getElementById('graph-score-count').innerText = d.graph_analysis.structure_score + '/100';

  const bfsChain = d.graph_analysis.bfs_order.length > 0 
    ? d.graph_analysis.bfs_order.join(' → ') 
    : 'NO KEYWORDS TRAVERSED';
  document.getElementById('graph-bfs-chain').innerText = bfsChain;

  const dfsChain = d.graph_analysis.dfs_order.length > 0 
    ? d.graph_analysis.dfs_order.join(' → ') 
    : 'NO KEYWORDS TRAVERSED';
  document.getElementById('graph-dfs-chain').innerText = dfsChain;

  renderSvgGraph(d.graph_analysis.graph, d.graph_analysis.keyword_freq);

  document.getElementById('csp-claims-count').innerText = d.csp.claims_count;
  document.getElementById('csp-consistency-score').innerText = d.csp.consistency_score + '/100';

  const claimsContainer = document.getElementById('csp-claims-list');
  claimsContainer.innerHTML = '';

  if (d.csp.claims.length === 0) {
    claimsContainer.innerHTML = '<div style="font-weight:700; color:#666;">No explicit factual claims detected to constrain.</div>';
  } else {
    d.csp.claims.forEach(c => {
      const item = document.createElement('div');
      item.className = `claim-item ${c.status === 'inconsistent' ? 'inconsistent' : ''}`;
      item.innerHTML = `
        <span class="claim-tag ${c.status}">${c.status.toUpperCase()}</span>
        <span style="font-size:12px; font-weight:700; flex:1;">${escapeHtml(c.claim)}</span>
      `;
      claimsContainer.appendChild(item);
    });
  }

  const aiCard = document.getElementById('ai-factcheck-card');
  const aiResultBox = document.getElementById('ai-factcheck-result');
  const aiSource = document.getElementById('ai-source');
  const aiStatus = document.getElementById('ai-status');
  const aiCompSection = document.getElementById('ai-comparison-section');
  const aiCompResult = document.getElementById('ai-comparison-result');

  if (d.ai_factcheck && d.ai_factcheck.enabled) {
    aiSource.innerText = d.ai_factcheck.source.toUpperCase();
    aiStatus.innerText = 'COMPLETE';
    aiResultBox.innerText = d.ai_factcheck.result || 'No result returned.';
    aiResultBox.style.whiteSpace = 'pre-wrap';

    if (d.ai_factcheck.comparison) {
      aiCompSection.style.display = 'block';
      aiCompResult.innerText = d.ai_factcheck.comparison;
      aiCompResult.style.whiteSpace = 'pre-wrap';
    } else {
      aiCompSection.style.display = 'none';
    }
  } else {
    aiSource.innerText = 'DISABLED';
    aiStatus.innerText = 'NO KEY';
    aiResultBox.innerText = 'ENTER A GEMINI API KEY IN THE INPUT CONSOLE TO ENABLE AI-POWERED FACT CHECKING.';
    aiResultBox.style.whiteSpace = 'normal';
    aiCompSection.style.display = 'none';
  }
}

function renderSvgGraph(adjList, freqMap) {
  const svg = document.getElementById('graph-svg');
  svg.innerHTML = '';

  const nodes = Object.keys(adjList);
  if (nodes.length === 0) {
    svg.innerHTML = '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="monospace" font-weight="bold" fill="#777">[NO KEYWORD TOPOLOGY DETECTED]</text>';
    return;
  }

  const width = svg.clientWidth || 800;
  const height = svg.clientHeight || 280;
  const padding = 40;

  const coords = {};
  const total = nodes.length;
  const centerX = width / 2;
  const centerY = height / 2;
  const rx = Math.max(120, (width - padding * 2) / 2);
  const ry = Math.max(70, (height - padding * 2) / 2);

  nodes.forEach((node, idx) => {
    const angle = (idx / total) * 2 * Math.PI - Math.PI / 2;
    const radFactor = (idx % 2 === 0) ? 0.95 : 0.65;
    const x = centerX + Math.cos(angle) * rx * radFactor;
    const y = centerY + Math.sin(angle) * ry * radFactor;
    coords[node] = { x, y };
  });

  const drawnEdges = new Set();
  nodes.forEach(u => {
    (adjList[u] || []).forEach(v => {
      const edgeKey = [u, v].sort().join('--');
      if (!drawnEdges.has(edgeKey) && coords[u] && coords[v]) {
        drawnEdges.add(edgeKey);
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', coords[u].x);
        line.setAttribute('y1', coords[u].y);
        line.setAttribute('x2', coords[v].x);
        line.setAttribute('y2', coords[v].y);
        line.setAttribute('stroke', '#000000');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('stroke-dasharray', '4 2');
        svg.appendChild(line);
      }
    });
  });

  nodes.forEach(node => {
    const { x, y } = coords[node];
    const freq = freqMap[node] || 1;
    const radius = Math.min(24, Math.max(15, 13 + freq * 2));

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.style.cursor = 'pointer';

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', x);
    circle.setAttribute('cy', y);
    circle.setAttribute('r', radius);
    circle.setAttribute('fill', '#ffe600');
    circle.setAttribute('stroke', '#000000');
    circle.setAttribute('stroke-width', '3');

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', x);
    text.setAttribute('y', y + 4);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-family', 'Space Mono, monospace');
    text.setAttribute('font-weight', 'bold');
    text.setAttribute('font-size', '10px');
    text.setAttribute('fill', '#000000');
    text.textContent = node.toUpperCase().slice(0, 8);

    g.appendChild(circle);
    g.appendChild(text);

    g.addEventListener('mouseenter', () => {
      circle.setAttribute('fill', '#0000ff');
      text.setAttribute('fill', '#ffffff');
    });
    g.addEventListener('mouseleave', () => {
      circle.setAttribute('fill', '#ffe600');
      text.setAttribute('fill', '#000000');
    });

    svg.appendChild(g);
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function loadHistory() {
  const container = document.getElementById('history-list');
  const countEl = document.getElementById('history-count');
  if (!container) return;

  try {
    const res = await fetch('/api/history');
    const data = await res.json();
    const history = data.history || [];
    
    countEl.innerText = data.total || 0;
    container.innerHTML = '';

    if (history.length === 0) {
      container.innerHTML = '<div style="font-weight:700; color:#666; padding:16px; text-align:center;">NO ANALYSIS RECORDS YET. RUN YOUR FIRST AUDIT ABOVE.</div>';
      return;
    }

    history.forEach(entry => {
      const row = document.createElement('div');
      row.className = 'history-row';
      
      let verdictClass = 'uncertain';
      if (entry.verdict === 'REAL') verdictClass = 'real';
      else if (entry.verdict === 'FAKE') verdictClass = 'fake';

      row.innerHTML = `
        <div class="history-row-header">
          <span class="history-id">#${entry.id}</span>
          <span class="history-timestamp">${entry.timestamp}</span>
          <span class="history-verdict-tag ${verdictClass}">${entry.verdict}</span>
          <span class="history-score">${entry.composite_score}/100</span>
          <button class="history-delete-btn" onclick="deleteHistoryEntry(${entry.id})" title="Delete">✕</button>
        </div>
        <div class="history-snippet">${escapeHtml(entry.text_snippet)}</div>
        <div class="history-meta">
          ML: ${entry.ml_prediction} (Real ${entry.real_probability}% / Fake ${entry.fake_probability}%) | 
          Credibility: ${entry.credibility_score}/100 | 
          Consistency: ${entry.consistency_score}/100
        </div>
      `;
      container.appendChild(row);
    });
  } catch (err) {
    container.innerHTML = '<div style="font-weight:700; color:#c70000; padding:16px;">FAILED TO LOAD HISTORY.</div>';
  }
}

async function clearHistory() {
  if (!confirm('CLEAR ALL ANALYSIS HISTORY? This action cannot be undone.')) return;
  
  try {
    await fetch('/api/history/clear', { method: 'POST' });
    loadHistory();
  } catch (err) {
    alert('Failed to clear history.');
  }
}

async function deleteHistoryEntry(id) {
  try {
    await fetch(`/api/history/${id}`, { method: 'DELETE' });
    loadHistory();
  } catch (err) {
    alert('Failed to delete entry.');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadHistory();
});
