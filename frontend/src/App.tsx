import { useEffect, useRef, useState, type FormEvent } from 'react';
import { AssistantAvatar, AcademicIllustration, Icon } from './Illustrations';
import { api, type Answer, type DocumentInfo, type Health, type SearchHit, type Source } from './api';

type View = 'Conversation' | 'Sources' | 'Documents' | 'Recherche';
interface Message { question: string; result: Answer }
const suggestions = [
  { label: 'Trouver un stage', icon: 'cap', question: 'Où sont publiées les offres de stage reçues par l’École ?' },
  { label: 'Dates des examens', icon: 'calendar', question: 'Quelles sont les dates des examens finaux pour 2026-2027 ?' },
  { label: 'Partir en mobilité', icon: 'globe', question: 'Combien de places de semestre d’études sont ouvertes pour 2027-2028 ?' },
  { label: 'Vie étudiante', icon: 'heart', question: 'Combien de membres fondateurs faut-il pour créer un club étudiant ?' },
];
const documentTitle = (d: DocumentInfo) => d.file.replace(/^\d+_/, '').replace(/_/g, ' ').replace(/\.pdf$/i, '');
function groupDocuments(documents: DocumentInfo[]) {
  const groups = [
    { title: 'Règlement des études', icon: 'documents', pattern: /reglement/i },
    { title: 'Stages et PFE', icon: 'cap', pattern: /stage|pfe/i },
    { title: 'Mobilité', icon: 'globe', pattern: /mobilite/i },
    { title: 'Calendrier', icon: 'calendar', pattern: /calendrier/i },
    { title: 'Autres documents disponibles', icon: 'sources', pattern: /./ },
  ];
  return groups.map((group, index) => ({ ...group, documents: documents.filter(d =>
    group.pattern.test(d.file) && !groups.slice(0, index).some(previous => previous.pattern.test(d.file)))
  })).filter(group => group.documents.length > 0);
}
const date = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString('fr-FR');
const score = (value: number) => value === -1 ? 'Contexte lié' : `Similarité cosinus ${value.toFixed(3)}`;

function SourceCard({ source, selected }: { source: Source; selected: boolean }) {
  return <article className={`source-card ${selected ? 'selected' : ''}`} id={`source-${source.id}`} tabIndex={-1}>
    <div className="card-meta"><span className="badge">[{source.id}] · PAGE {source.page}</span><span>{score(source.score)}</span></div>
    <h3>{source.section}</h3><p className="filename">{source.file}</p>
    <p className="metadata">{source.reference} · {date(source.date)}</p><blockquote>{source.excerpt}</blockquote>
  </article>;
}

export default function App() {
  const [view, setView] = useState<View>('Conversation');
  const [health, setHealth] = useState<Health | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [topK, setTopK] = useState(5);
  const [filter, setFilter] = useState('');
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [strategy, setStrategy] = useState('structural');
  const [size, setSize] = useState(500);
  const [overlap, setOverlap] = useState(100);
  const [notice, setNotice] = useState('');
  const bottom = useRef<HTMLDivElement>(null);
  const questionInput = useRef<HTMLTextAreaElement>(null);
  async function refresh() {
    const [h, d] = await Promise.all([api.health(), api.documents()]);
    setHealth(h); setDocuments(d);
  }
  useEffect(() => { refresh().catch(e => setError((e as Error).message)); }, []);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' }); }, [messages, busy]);
  useEffect(() => { if (view === 'Sources' && selected !== null) document.getElementById(`source-${selected}`)?.focus(); }, [view, selected]);
  function openSource(id: number, all: Source[]) { setSources(all); setSelected(id); setView('Sources'); }
  async function submit(event?: FormEvent, preset?: string) {
    event?.preventDefault(); const text = (preset ?? question).trim(); if (!text || busy) return;
    setBusy(true); setError('');
    try {
      const query = { question: text, top_k: topK, filters: { type: filter || null } };
      if (view === 'Recherche') { const result = await api.search(query); setHits(result.hits); }
      else { const result = await api.ask(query); setMessages(previous => [...previous, { question: text, result }]); setSources(result.sources); setQuestion(''); }
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function ingest() {
    if (busy) return; setBusy(true); setError(''); setNotice('');
    try { const result = await api.ingest(strategy, size, overlap); setNotice(`${result.chunks} fragments indexés${result.reused ? ' · index déjà à jour' : ''}.`); await refresh(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  function answerText(message: Message) { return message.result.answer.split(/(\[\d+\])/g).map((part, index) => /^\[\d+\]$/.test(part) ? <button className="citation" key={index} onClick={() => openSource(Number(part.slice(1, -1)), message.result.sources)} aria-label={`Afficher la source ${part}`}>{part}</button> : part); }
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#" onClick={e => { e.preventDefault(); setView('Conversation'); }}><span className="brand-mark">H</span><span>EIH<small>ÉCOLE D’INGÉNIEURS HÉLIANTHE</small></span></a>
      <div className="sidebar-assistant"><Icon name="cap" size={30}/><div><strong>Assistant Scolarité</strong><span>Votre assistant pour la scolarité</span></div></div>
      <nav aria-label="Navigation principale">{(['Conversation', 'Sources', 'Documents', 'Recherche'] as View[]).map((item, index) => <button disabled={busy} aria-current={view === item ? 'page' : undefined} className={view === item ? 'active' : ''} key={item} onClick={() => { setView(item); setError(''); }}><Icon name={['chat', 'sources', 'documents', 'search'][index]}/><span>{item}</span>{item === 'Documents' && <em>{documents.length}</em>}{view === item && <span className="nav-indicator"/>}</button>)}</nav>
      <div className="sidebar-note"><AcademicIllustration compact/><h3>Des réponses fiables,<br/>avec leurs sources.</h3></div>
      <footer><span className={`status-dot ${health?.chunks ? 'ready' : ''}`} />{health ? `${health.chunks} fragments indexés` : 'Backend non connecté'}<small>Projet pédagogique · 2026–2027</small></footer>
    </aside>
    <main>
      <header className="topbar"><div className="header-title">Assistant Scolarité <span>· EIH</span></div><div className="header-actions"><span className="private-label"><Icon name="shield" size={15}/>Corpus officiel</span><span className="user-avatar" role="img" aria-label="Profil utilisateur générique"><Icon name="user"/></span></div></header>
      <div className={`workspace ${view === 'Conversation' ? 'conversation-workspace' : ''}`}>
        <div className="content">
          {view !== 'Conversation' && <div className="page-heading"><div><p className="eyebrow">VOTRE ÉCOLE, EN PLUS CLAIR</p><h1>{view === 'Recherche' ? 'Explorer les passages' : view === 'Documents' ? 'La bibliothèque officielle' : 'À la source de la réponse'}</h1></div><span className="year">2026–2027</span></div>}
          {error && <div role="alert" className="error">{error}</div>}
          {notice && <div role="status" className="notice">{notice}</div>}
          {health && !health.openai_configured && <div className="notice setup-notice"><Icon name="help" size={18}/><span>Ajoutez votre clé OpenAI dans backend/.env, puis redémarrez le serveur pour activer l’indexation et les réponses.</span></div>}
          {view === 'Conversation' && <>
            <section className={`welcome ${messages.length ? 'welcome-condensed' : ''}`}>
              <div className="welcome-portrait"><AssistantAvatar/><span className="portrait-sparkle sparkle-one">✧</span><span className="portrait-sparkle sparkle-two">✦</span></div>
              <div className="welcome-copy"><p className="eyebrow">VOTRE ÉCOLE, EN PLUS CLAIR</p><h1>Comment pouvons-nous vous aider <span>aujourd’hui ?</span></h1><p>Posez votre question sur les stages, examens, mobilité ou vie étudiante.</p></div>
            </section>
            <div className={`conversation-body ${messages.length ? 'has-messages' : ''}`}>
              <form className="composer" onSubmit={submit}><span className="composer-star"><Icon name="sparkle" size={23}/></span><label className="sr-only" htmlFor="chat-question">Votre question</label><textarea ref={questionInput} id="chat-question" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Posez votre question…" maxLength={2000} rows={1} disabled={busy}/><button className="send" disabled={busy || !question.trim()} aria-label="Envoyer la question">{busy ? <span className="send-loading"/> : <Icon name="arrow" size={21}/>}</button></form>
              <div className="suggestion-row"><p className="suggestion-title"><Icon name="sparkle" size={19}/>Suggestions pour commencer</p><div className="suggestions">{suggestions.map(s => <button key={s.label} disabled={busy} onClick={() => { setQuestion(s.question); questionInput.current?.focus(); }}><Icon name={s.icon} size={17}/>{s.label}</button>)}</div></div>
              <p className="composer-note"><Icon name="shield" size={13}/>Des réponses fondées sur vos documents. Des sources pour les vérifier.</p>

              {messages.length > 0 && <div className="chat" aria-live="polite">{messages.map((m, i) => <section key={i} className="exchange">
                <div className="student-message"><div className="question-bubble">{m.question}</div><span className="user-avatar" role="img" aria-label="Vous"><Icon name="user" size={19}/></span></div>
                <div className={`assistant-message ${m.result.found ? '' : 'refusal'}`}><AssistantAvatar small/><div className="assistant-message-body"><div className="answer-label"><strong>Assistant Scolarité EIH</strong><span className="ai-badge">Assistant IA</span></div><div className="answer"><p>{answerText(m)}</p>{!m.result.found && <span className="refusal-label">Information non trouvée dans le corpus</span>}
                  {m.result.sources.length > 0 && <div className="inline-sources"><div className="inline-sources-heading"><Icon name="sources" size={15}/><span>Sources de cette réponse</span></div>{m.result.sources.map(s => <button className="inline-source" key={s.chunk_id} onClick={() => openSource(s.id, m.result.sources)}><span className="inline-source-number">[{s.id}]</span><span><strong>{s.file}</strong><span className="inline-source-meta">Page {s.page} · {date(s.date)} · {s.reference}</span><span className="inline-source-excerpt">{s.excerpt}</span></span><Icon name="chevron" size={15}/></button>)}</div>}
                  <div className="answer-footer">{m.result.sources.length > 0 && <button className="text-button" onClick={() => { setSources(m.result.sources); setSelected(null); setView('Sources'); }}>Consulter toutes les sources <Icon name="chevron" size={13}/></button>}<small>{(m.result.latency_ms/1000).toFixed(1)} s{m.result.invalid_citations.length > 0 ? ' · Citations invalides détectées' : ''}</small></div>
                </div></div></div>
              </section>)}<div ref={bottom}/></div>}
              {busy && <div className="loading" role="status"><AssistantAvatar small/><div><strong>Un instant, je consulte les documents…</strong><span className="typing-dots"><i/><i/><i/></span></div></div>}
              {!messages.length && <div className="conversation-empty"><span className="empty-rule"/><span>Un espace pour toutes vos questions</span><span className="empty-rule"/><div className="empty-reassurance"><span><Icon name="documents" size={16}/>Documents officiels</span><span><Icon name="sources" size={16}/>Sources consultables</span><span><Icon name="cap" size={17}/>Pensé pour les étudiants</span></div></div>}
            </div>
          </>}
          {view === 'Sources' && <div className="source-page"><p className="intro">Les extraits exacts associés à la réponse sélectionnée.</p>{sources.length ? sources.map(s => <SourceCard key={s.chunk_id} source={s} selected={selected === s.id}/>) : <div className="empty"><Icon name="sources" size={30}/><p>Les sources apparaîtront après une réponse documentée. Cliquez sur une citation dans la conversation.</p></div>}</div>}
          {view === 'Documents' && <><p className="intro">Les documents réellement présents dans l’index actif.</p><div className="document-grid">{documents.map((d, i) => <article className="document-card" key={d.file}><div className="document-top"><span className="doc-symbol"><Icon name="documents" size={25}/></span><span>DOCUMENT {String(i+1).padStart(2,'0')}</span></div><h2>{d.file.replace(/^\d+_/, '').replace(/_/g, ' ').replace('.pdf', '')}</h2><p>{d.type}</p><p className="metadata">{d.reference}<br/>{date(d.date)} · Version {d.version}</p><p className="document-status">{d.status}</p><span className="badge">{d.chunks} fragments</span></article>)}</div>{!documents.length && <div className="empty"><Icon name="documents" size={30}/><p>Aucun document indexé. Lancez l’ingestion des 7 PDF ci-dessous.</p></div>}
            <section className="ingestion"><div className="section-title-icon"><Icon name="sparkle"/><h2>Préparer l’index documentaire</h2></div><p>Cette opération utilise les embeddings OpenAI et peut entraîner un coût API.</p><div className="controls"><label>Découpage<select value={strategy} onChange={e => setStrategy(e.target.value)} disabled={busy}><option value="structural">Structurel</option><option value="fixed">Taille fixe</option></select></label><label>Taille<input type="number" min={1} max={12000} value={size} onChange={e => setSize(+e.target.value)} disabled={busy}/></label><label>Chevauchement<input type="number" min={0} max={size-1} value={overlap} onChange={e => setOverlap(+e.target.value)} disabled={busy}/></label><button className="primary" disabled={busy || size <= 0 || overlap < 0 || overlap >= size} onClick={ingest}>{busy ? 'Indexation…' : 'Indexer les documents'}</button></div></section></>}
          {view === 'Recherche' && <><p className="intro">Inspectez la recherche sémantique sans génération de réponse. La question utilise un appel embedding OpenAI.</p><form onSubmit={submit} className="search-form"><label>Question<input value={question} maxLength={2000} onChange={e => setQuestion(e.target.value)} disabled={busy}/></label><div className="controls"><label>Top-k<input type="number" min={1} max={30} value={topK} onChange={e => setTopK(+e.target.value)} disabled={busy}/></label><label>Type de document<select aria-label="Type de document" value={filter} onChange={e => setFilter(e.target.value)} disabled={busy}><option value="">Tous les types</option>{[...new Set(documents.map(d => d.type))].map(t => <option key={t}>{t}</option>)}</select></label><button className="primary" disabled={busy || !question.trim() || topK < 1 || topK > 30}>{busy ? 'Recherche…' : 'Rechercher'}</button></div></form>{hits?.map((h, i) => <SourceCard key={h.chunk.id} selected={false} source={{ id:i+1, chunk_id:h.chunk.id, file:h.chunk.file, reference:h.chunk.reference, date:h.chunk.date, page:h.chunk.page, section:h.chunk.section, excerpt:h.chunk.text, score:h.score }}/ >)}{hits?.length === 0 && <div className="empty"><Icon name="search" size={30}/><p>Aucun passage trouvé dans l’index pour ce filtre.</p></div>}</>}
        </div>
        {view === 'Conversation' && <aside className="right-panel" aria-label="Informations documentaires"><details className="right-panel-details" open><summary><Icon name="documents" size={17}/>À propos de vos sources<Icon name="chevron" size={14}/></summary><div className="right-panel-cards">
          <figure className="campus-card"><img src="/images/campus-eih.png" alt="Illustration décorative d’un campus imaginaire de l’EIH"/><figcaption>Illustration du campus fictif</figcaption></figure>
          <section className="principal-sources"><h2><Icon name="sources" size={23}/>Sources principales <span>{documents.length}</span></h2><p>Corpus officiel de l’École : règlements, calendriers, guides et procédures.</p>{documents.length > 0 ? <div className="principal-source-list source-tiles">{groupDocuments(documents).map((group, index) => <button key={group.title} title={group.documents.map(documentTitle).join(' · ')} disabled={busy} onClick={() => setView('Documents')}><span className={`source-type-icon tone-${index % 4}`}><Icon name={group.icon} size={18}/></span><span><strong>{group.title}</strong><small>{group.documents.length} document{group.documents.length > 1 ? 's' : ''}</small></span><Icon name="chevron" size={13}/></button>)}</div> : <div className="panel-empty"><Icon name="documents" size={22}/><p>Les sources seront affichées après l’indexation de vos documents.</p></div>}</section>
          <section className="help-card"><span className="help-icon"><Icon name="help" size={21}/></span><div><h2>Besoin d’aide ?</h2><p>Consultez les documents officiels ou contactez le service de scolarité.</p><button disabled={busy} className="text-button help-link" onClick={() => setView('Documents')}>Consulter les documents<Icon name="sources" size={14}/></button></div></section>
          <p className="panel-footnote">Votre scolarité mérite des réponses claires.</p>
        </div></details></aside>}
      </div>
    </main>
  </div>;
}
