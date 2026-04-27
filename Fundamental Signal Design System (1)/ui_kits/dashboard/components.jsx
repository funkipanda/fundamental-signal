// UI kit components. Exported to window for use by index.html.
const { useState, useMemo } = React;

const fmtPct = (v, d=1) => v == null ? "N/A" : `${(v*100).toFixed(d)}%`;
const fmtX   = (v, d=1) => v == null ? "N/A" : `${v.toFixed(d)}x`;
const fmtUSD = (v) => v == null ? "—" : `$${v.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}`;

const SIG = {
  UNDERVALUED: { cls: "u", icon: "▼", label: "UNDERVALUED" },
  OVERVALUED:  { cls: "o", icon: "▲", label: "OVERVALUED" },
  VALUE_TRAP:  { cls: "t", icon: "⚠", label: "VALUE_TRAP" },
  QUALITY_PREMIUM: { cls: "p", icon: "★", label: "QUALITY_PREMIUM" },
  FAIR_VALUE:  { cls: "f", icon: "―", label: "FAIR_VALUE" },
};

function divergence(stock, bench, direction="lower") {
  if (stock == null || bench == null) return null;
  const pct = (stock - bench) / Math.abs(bench) * 100;
  const fav = direction === "lower" ? -pct : pct;
  let signal = "neutral";
  if (fav > 15) signal = "undervalued";
  else if (fav < -15) signal = "overvalued";
  return { pct, signal };
}

function Ic({d, poly, circle, more, children, cls="ic"}) {
  return React.createElement("svg", {className:cls, viewBox:"0 0 24 24"}, children);
}

function IconSearch(){return(<svg className="ic" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>)}
function IconFilter(){return(<svg className="ic" viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>)}
function IconDownload(){return(<svg className="ic" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>)}
function IconUpload(){return(<svg className="ic" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>)}
function IconPlus(){return(<svg className="ic" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>)}
function IconX(){return(<svg className="ic" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>)}
function IconPlay(){return(<svg className="ic" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>)}
function IconRefresh(){return(<svg className="ic" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>)}
function IconHome(){return(<svg className="ic" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>)}
function IconList(){return(<svg className="ic" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>)}
function IconBookmark(){return(<svg className="ic" viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>)}
function IconSettings(){return(<svg className="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>)}

function TopBar({ onRun, onOpenWatchlist }) {
  return (
    <div className="topbar">
      <div className="brand">
        <img src="../../assets/monogram.svg" alt=""/>
        <div>
          <div className="name">FUNDAMENTAL <span className="sub">SIGNAL</span></div>
        </div>
      </div>
      <div className="search">
        <IconSearch/>
        <input placeholder="Search ticker, sector, flag…"/>
      </div>
      <div className="spacer"/>
      <span className="pill"><span className="dot"/>Live · yfinance OK</span>
      <span className="pill">2026-04-23 14:32 ET</span>
      <button className="ico-btn" title="Settings"><IconSettings/></button>
    </div>
  );
}

function Rail() {
  return (
    <div className="rail">
      <div className="item" title="Home"><IconHome/></div>
      <div className="item active" title="Screener"><IconList/></div>
      <div className="item" title="Watchlists"><IconBookmark/></div>
      <div className="item" title="Exports"><IconDownload/></div>
    </div>
  );
}

function Counts({ rows }) {
  const counts = useMemo(() => {
    const c = { UNDERVALUED:0, OVERVALUED:0, VALUE_TRAP:0, QUALITY_PREMIUM:0, FAIR_VALUE:0 };
    rows.forEach(r => c[r.classification]++);
    return c;
  }, [rows]);
  return (
    <div className="counts">
      <div className="count u"><span className="g">▼</span><div><div className="n">{counts.UNDERVALUED}</div><div className="l">Undervalued</div></div></div>
      <div className="count o"><span className="g">▲</span><div><div className="n">{counts.OVERVALUED}</div><div className="l">Overvalued</div></div></div>
      <div className="count t"><span className="g">⚠</span><div><div className="n">{counts.VALUE_TRAP}</div><div className="l">Value trap</div></div></div>
      <div className="count p"><span className="g">★</span><div><div className="n">{counts.QUALITY_PREMIUM}</div><div className="l">Quality premium</div></div></div>
      <div className="count f"><span className="g">―</span><div><div className="n">{counts.FAIR_VALUE}</div><div className="l">Fair value</div></div></div>
    </div>
  );
}

function Toolbar({ filter, setFilter, compact, setCompact, onOpenWatchlist }) {
  const filters = ["ALL","UNDERVALUED","OVERVALUED","VALUE_TRAP","QUALITY_PREMIUM","FAIR_VALUE"];
  return (
    <div className="toolbar">
      <div className="seg">
        {filters.map(f => (
          <button key={f} className={filter===f?"on":""} onClick={()=>setFilter(f)}>{f.replace("_"," ")}</button>
        ))}
      </div>
      <div className="div"/>
      <button className="btn btn-ghost"><IconFilter/> Sector</button>
      <button className="btn btn-ghost"><IconFilter/> Confidence</button>
      <div className="spacer" style={{flex:1}}/>
      <span className="chip">Density</span>
      <div className="seg">
        <button className={!compact?"on":""} onClick={()=>setCompact(false)}>Default</button>
        <button className={compact?"on":""} onClick={()=>setCompact(true)}>Compact</button>
      </div>
      <div className="div"/>
      <button className="btn btn-secondary" onClick={onOpenWatchlist}><IconPlus/> Edit watchlist</button>
      <button className="btn btn-secondary"><IconDownload/> Export .md</button>
      <button className="btn btn-primary"><IconRefresh/> Rerun screen</button>
    </div>
  );
}

function SigBadge({ classification }) {
  const s = SIG[classification];
  return <span className={`sig ${s.cls}`}>{s.icon} {s.label}</span>;
}

function CellVsSector({ value, bench, direction="lower", format="x" }) {
  if (value == null) return <span className="cell-na">N/A</span>;
  const fmt = (v) => format === "%" ? `${(v*100).toFixed(1)}%` : `${v.toFixed(1)}x`;
  const div = bench != null ? divergence(value, bench, direction) : null;
  const cls = div?.signal === "undervalued" ? "cell-cheap" : div?.signal === "overvalued" ? "cell-expensive" : "";
  return (
    <span>
      <span className={cls}>{fmt(value)}</span>
      {bench != null && <span style={{color:"var(--fs-fg-dim)", marginLeft:4}}>({bench.toFixed(0)})</span>}
    </span>
  );
}

function SummaryTable({ rows, selected, onSelect }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <span className="eyebrow">Screen · {rows.length} tickers</span>
        <div className="actions">
          <button className="btn btn-ghost" style={{fontSize:10}}>SIGNAL ↓</button>
        </div>
      </div>
      <div style={{maxHeight:"calc(100vh - 340px)", overflow:"auto"}}>
        <table className="sig-table">
          <thead><tr>
            <th>Ticker</th>
            <th>Signal</th>
            <th>Conf.</th>
            <th>Sector</th>
            <th className="num">Fwd P/E <span className="sub">(sect)</span></th>
            <th className="num">EV/EBITDA <span className="sub">(sect)</span></th>
            <th className="num">FCF Yld</th>
            <th className="num">ROE</th>
            <th className="num">D/E</th>
            <th className="num">Price</th>
            <th className="num">Chg %</th>
          </tr></thead>
          <tbody>
            {rows.map(r => {
              const s = SIG[r.classification];
              const selCls = selected === r.ticker ? "sel" : "";
              return (
                <tr key={r.ticker} className={`${s.cls} ${selCls}`} onClick={()=>onSelect(r.ticker)}>
                  <td className="tk">{r.ticker}</td>
                  <td><SigBadge classification={r.classification}/></td>
                  <td><span className={`conf ${r.confidence==="high"?"high":r.confidence==="medium"?"med":"low"}`}><span className="d"/>{r.confidence}</span></td>
                  <td><span className="sect">{r.sector}</span></td>
                  <td className="num"><CellVsSector value={r.metrics.forward_pe} bench={r.bench?.pe}/></td>
                  <td className="num"><CellVsSector value={r.metrics.ev_ebitda} bench={r.bench?.ev_ebitda}/></td>
                  <td className="num">{r.metrics.fcf_yield == null ? <span className="cell-na">N/A</span> : fmtPct(r.metrics.fcf_yield)}</td>
                  <td className="num">{fmtPct(r.metrics.roe)}</td>
                  <td className="num">{r.metrics.debt_equity == null ? <span className="cell-na">N/A</span> : fmtX(r.metrics.debt_equity)}</td>
                  <td className="num">{fmtUSD(r.price)}</td>
                  <td className={`num ${r.change>=0?"cell-cheap":"cell-expensive"}`}>{r.change>=0?"+":""}{r.changePct.toFixed(2)}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DetailCard({ row }) {
  if (!row) return <div className="panel"><div className="empty">Select a ticker<div className="mono">Click any row to see details</div></div></div>;
  const s = SIG[row.classification];
  const r52 = row.range52;
  const pos = r52 ? Math.max(0, Math.min(100, ((row.price - r52.low) / (r52.high - r52.low)) * 100)) : 50;
  const ma50pos = r52 ? ((r52.ma50 - r52.low) / (r52.high - r52.low)) * 100 : 50;
  const ma200pos = r52 ? ((r52.ma200 - r52.low) / (r52.high - r52.low)) * 100 : 50;
  const dv_pe = divergence(row.metrics.forward_pe, row.bench?.pe, "lower");
  const dv_ev = divergence(row.metrics.ev_ebitda, row.bench?.ev_ebitda, "lower");

  return (
    <div className="panel detail">
      <div className="detail-head">
        <div className="row1">
          <span className="tkr-lg">{row.ticker}</span>
          <span className="name">— {row.name}</span>
        </div>
        <div className="meta">{row.sector} · {row.industry} · Mkt cap ${row.mcap}</div>
        <div className="row2">
          <div>
            <div className="price">{fmtUSD(row.price)}</div>
            <div className={`chg ${row.change<0?"down":""}`}>
              {row.change>=0?"+":""}{row.change.toFixed(2)} ({row.change>=0?"+":""}{row.changePct.toFixed(2)}%) {row.change>=0?"▲":"▼"}
            </div>
          </div>
          <div style={{textAlign:"right"}}>
            <span className={`badge-lg ${s.cls}`}>{s.icon} {s.label}</span>
            <div style={{marginTop:6}}>
              <span className={`conf ${row.confidence==="high"?"high":row.confidence==="medium"?"med":"low"}`}><span className="d"/>{row.confidence} conf</span>
            </div>
          </div>
        </div>
      </div>

      <div className="section">
        <div className="eyebrow">Valuation vs. sector</div>
        <div className="metric-row">
          <span className="k">Forward P/E</span>
          <span className="v">{fmtX(row.metrics.forward_pe)}</span>
          <span className="vs">{row.bench?.pe ? `vs ${row.bench.pe.toFixed(1)}x sector` : ""}</span>
        </div>
        {dv_pe && <div style={{fontSize:11, fontFamily:"var(--fs-font-mono)", color: dv_pe.signal==="undervalued"?"var(--fs-signal-undervalued)": dv_pe.signal==="overvalued"?"var(--fs-signal-overvalued)":"var(--fs-fg-muted)"}}>{dv_pe.pct>0?"+":""}{dv_pe.pct.toFixed(1)}% {dv_pe.signal==="undervalued"?"▼ cheap":dv_pe.signal==="overvalued"?"▲ expensive":"—"}</div>}
        <div className="metric-row" style={{marginTop:6}}>
          <span className="k">EV/EBITDA</span>
          <span className="v">{row.suppressed?.includes("ev_ebitda") ? <span className="cell-na">N/A</span> : fmtX(row.metrics.ev_ebitda)}</span>
          <span className="vs">{row.suppressed?.includes("ev_ebitda") ? "suppressed (financials)" : row.bench?.ev_ebitda ? `vs ${row.bench.ev_ebitda.toFixed(1)}x sector` : ""}</span>
        </div>
        <div className="metric-row">
          <span className="k">FCF Yield</span>
          <span className="v">{row.metrics.fcf_yield == null ? <span className="cell-na">N/A</span> : fmtPct(row.metrics.fcf_yield)}</span>
          <span className="vs">vs 5.0% baseline</span>
        </div>
      </div>

      <div className="section">
        <div className="eyebrow">Quality filters</div>
        <div className="check-row"><span className="k">ROE</span><span className="v">{fmtPct(row.metrics.roe)}</span><span className="thr">≥ 10.0%</span><span className={`ico ${row.metrics.roe>=0.10?"ok":"no"}`} style={{color: row.metrics.roe>=0.10?"var(--fs-signal-undervalued)":"var(--fs-signal-overvalued)"}}>{row.metrics.roe>=0.10?"✓":"✗"}</span></div>
        <div className="check-row"><span className="k">CF Quality</span><span className="v">{fmtX(row.metrics.cf_quality)}</span><span className="thr">≥ 0.8x</span><span style={{color: row.metrics.cf_quality>=0.8?"var(--fs-signal-undervalued)":"var(--fs-signal-overvalued)"}}>{row.metrics.cf_quality>=0.8?"✓":"✗"}</span></div>
        <div className="check-row"><span className="k">D/E Ratio</span>
          <span className="v">{row.metrics.debt_equity == null ? <span className="cell-na">N/A</span> : fmtX(row.metrics.debt_equity)}</span>
          <span className="thr">{row.deThreshold === null ? "n/a banks" : "≤ 2.0x"}</span>
          <span style={{color: row.deThreshold===null ? "var(--fs-fg-dim)" : row.metrics.debt_equity<=2.0?"var(--fs-signal-undervalued)":"var(--fs-signal-overvalued)"}}>{row.deThreshold===null ? "―" : row.metrics.debt_equity<=2.0 ? "✓" : "✗"}</span>
        </div>
      </div>

      <div className="section">
        <div className="eyebrow">Price context · 52-week</div>
        <div className="range-track">
          <div className="ma" style={{left:`${ma200pos}%`}} title="200-day MA"/>
          <div className="ma" style={{left:`${ma50pos}%`, background:"var(--fs-fg-strong)"}} title="50-day MA"/>
          <div className="cur" style={{left:`${pos}%`}} data-pct={`${pos.toFixed(0)}%`}/>
        </div>
        <div className="range-labels">
          <span>{fmtUSD(r52.low)}</span>
          <span>50d {fmtUSD(r52.ma50)} · 200d {fmtUSD(r52.ma200)}</span>
          <span>{fmtUSD(r52.high)}</span>
        </div>
      </div>

      <div className="section">
        <div className="eyebrow">Flags</div>
        {row.flags.map((f, i) => (
          <div key={i} className={`flag ${f.kind}`}>
            {f.caps && <span className="caps">{f.caps}</span>} <span>{f.caps ? f.text.replace(f.caps,"").trim() : f.text}</span>
          </div>
        ))}
        {row.sectorNote && (
          <div style={{marginTop:10, fontFamily:"var(--fs-font-sans)", fontSize:11, color:"var(--fs-fg-dim)", fontStyle:"italic"}}>
            Sector note: {row.sectorNote}
          </div>
        )}
      </div>
    </div>
  );
}

function WatchlistModal({ open, onClose, onAdd }) {
  const [text, setText] = useState("AAPL\nMSFT\nJPM\nXOM\nINTC\nTSLA\nGOOGL\nT\nJNJ");
  if (!open) return null;
  return (
    <div className="scrim" onClick={onClose}>
      <div className="modal" onClick={e=>e.stopPropagation()}>
        <div className="modal-head">
          <div className="t">Edit watchlist</div>
          <button className="ico-btn" onClick={onClose}><IconX/></button>
        </div>
        <div className="modal-body">
          <div className="lbl">Tickers · one per line</div>
          <textarea value={text} onChange={e=>setText(e.target.value)} spellCheck="false"/>
          <div className="dropzone">
            <div><IconUpload/></div>
            <div style={{marginTop:6}}>Drop .txt or .csv · or click to browse</div>
          </div>
        </div>
        <div className="modal-foot">
          <div className="hint">{text.split("\n").filter(t=>t.trim()).length} tickers · ~{(text.split("\n").filter(t=>t.trim()).length * 1.5).toFixed(0)}s to fetch</div>
          <div className="actions">
            <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button className="btn btn-primary" onClick={()=>{onAdd(text.split("\n").map(t=>t.trim()).filter(Boolean));onClose();}}><IconPlay/> Run screen</button>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  TopBar, Rail, Counts, Toolbar, SummaryTable, DetailCard, WatchlistModal, SIG, fmtPct, fmtX, fmtUSD,
});
