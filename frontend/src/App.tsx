import { useState, useEffect } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { API_BASE_URL, fetchAvailableModels, type ModelConfig } from "@/lib/api";
import { mdComponents } from "@/components/ChatMessagesView";
import "./deepvalue.css";

type Fact = { value: number; unit: string; tag: string; filed: string; accession: string };
type Financial = { period_end: string; filed: string; url: string; metrics: Record<string, Fact> };
type Evidence = { title: string; url: string; category: string; published: string; excerpt: string; kind: string; date_basis: string };
type ResearchState = {
  messages: Message[];
  request: Record<string, unknown>;
  report: string;
  financials: Financial[];
  evidence: Record<string, Evidence>;
  financial_issues: string[];
  review: { status?: string; missing_categories?: string[] };
  valuation: { status?: string; reason?: string; normalized_eps?: number; scenarios?: { label: string; pe: number; value_per_share: number }[] };
};
const stages: Record<string, string> = {
  define_scope: "确认公司与截止日", collect_financials: "获取并校验 SEC 财报",
  plan_research: "规划资料采集", collect_context: "采集新闻、行业与政策",
  normalize_evidence: "整理证据与日期", validate_evidence: "检查关键数据",
  analyze_business: "分析经营与风险", calculate_valuation: "计算估值情景",
  review_thesis: "核验判断与引用", write_report: "完成研究报告",
};

export default function App() {
  const [ticker, setTicker] = useState("CAT");
  const [cik, setCik] = useState("18230");
  const [asOf, setAsOf] = useState("2025-03-01");
  const [years, setYears] = useState(3);
  const [rounds, setRounds] = useState(2);
  const [focus, setFocus] = useState("分析盈利质量、行业周期与资本配置，主动寻找反面证据。");
  const [multiples, setMultiples] = useState([10, 15, 20]);
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [model, setModel] = useState("");
  const [error, setError] = useState("");
  const [events, setEvents] = useState<string[]>([]);
  const [view, setView] = useState("report");
  const [submitted, setSubmitted] = useState(false);
  const [activeScope, setActiveScope] = useState({ticker: "", asOf: ""});

  useEffect(() => {
    fetchAvailableModels().then(list => {
      if (!list.length) throw new Error("后端未配置可用模型");
      setModels(list);
      setModel(list[0].model_id);
    }).catch(e => setError("模型列表加载失败：" + e.message));
  }, []);

  const thread = useStream<ResearchState>({
    apiUrl: API_BASE_URL, assistantId: "deepvalue", messagesKey: "messages",
    onUpdateEvent: (event: Record<string, unknown>) => {
      Object.keys(event).forEach(key => {
        if (stages[key]) setEvents(previous => [...previous, stages[key]]);
      });
    },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : String(e)),
  });
  const values = thread.values;
  const report = values.report || "";
  const evidence = Object.entries(values.evidence || {});
  const financials = values.financials || [];
  const busy = thread.isLoading;
  const limited = !!values.financial_issues?.length || values.review?.status === "limited";

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!(multiples[0] > 0 && multiples[0] < multiples[1] && multiples[1] < multiples[2])) {
      setError("市盈率假设须满足 0 < 低情景 < 基准 < 高情景。"); return;
    }
    setError(""); setEvents([]); setSubmitted(true); setView("report");
    setActiveScope({ticker, asOf});
    try {
      await thread.submit({ request: {
        ticker, cik, as_of: asOf, industry: "machinery", years, max_rounds: rounds,
        pe_low: multiples[0], pe_base: multiples[1], pe_high: multiples[2],
        focus, model,
      }}, { config: { recursion_limit: 40 } });
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  function download(kind: "md" | "json") {
    const body = kind === "md" ? report : JSON.stringify(values, null, 2);
    const url = URL.createObjectURL(new Blob([body], {type: kind === "md" ? "text/markdown;charset=utf-8" : "application/json"}));
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = `DeepValue-${activeScope.ticker}-${activeScope.asOf}.${kind}`;
    anchor.click(); URL.revokeObjectURL(url);
  }

  return <div className="dv-shell">
    <header className="dv-header">
      <a className="dv-brand" href="/app/"><span className="dv-mark">DV</span> DeepValue <span className="dv-version">研究工作台 / V1</span></a>
      <span className="dv-status">SEC 财务事实 · 可追溯证据 · 可复算情景</span>
    </header>
    <main className="dv-layout">
      <aside className="dv-panel">
        <div className="dv-kicker">研究范围</div>
        <h1>从一家公司开始。</h1>
        <p className="dv-muted">美股机械制造业 · SIC 3500–3599<br/>默认示例：Caterpillar / CAT</p>
        <form onSubmit={submit}>
          <fieldset disabled={busy}>
            <div className="dv-pair">
              <label>证券代码<input required aria-label="证券代码" value={ticker} onChange={e=>setTicker(e.target.value.toUpperCase())} pattern="[A-Z][A-Z0-9.\-]{0,9}" /></label>
              <label>SEC CIK<input required aria-label="SEC CIK" value={cik} onChange={e=>setCik(e.target.value)} pattern="[0-9]{1,10}" /></label>
            </div>
            <label>固定研究截止日<input aria-label="固定研究截止日" required type="date" min="2010-01-01" value={asOf} onChange={e=>setAsOf(e.target.value)} /></label>
            <small>以美国东部日终为界，财报须已披露。</small>
            <div className="dv-pair">
              <label>历史财年<select value={years} onChange={e=>setYears(Number(e.target.value))}><option value={3}>3 年</option><option value={4}>4 年</option><option value={5}>5 年</option></select></label>
              <label>采集预算<select value={rounds} onChange={e=>setRounds(Number(e.target.value))}><option value={1}>1 轮</option><option value={2}>最多 2 轮</option></select></label>
            </div>
            <label>分析模型<select required value={model} onChange={e=>setModel(e.target.value)}><option value="" disabled>请选择模型</option>{models.map(m=><option key={m.model_id} value={m.model_id}>{m.display_name}</option>)}</select></label>
            <div className="dv-divider" />
            <div className="dv-kicker">估值假设 · 用户设定</div>
            <p className="dv-muted">三年稀释 EPS 中位数 × 市盈率。<br/>不代表同业倍数或目标价。</p>
            <div className="dv-triple">{["低情景 PE", "基准 PE", "高情景 PE"].map((label,index)=><label key={label}>{label}<input aria-label={label} type="number" required min="0.1" max="80" step="0.1" value={multiples[index]} onChange={e=>setMultiples(previous=>previous.map((v,i)=>i===index?Number(e.target.value):v))}/></label>)}</div>
            <label>研究重点<textarea rows={3} maxLength={1000} value={focus} onChange={e=>setFocus(e.target.value)} /></label>
            <button className="dv-primary" disabled={busy || !model} type="submit">{busy ? "研究进行中…" : "开始研究 →"}</button>
          </fieldset>
          {busy && <button type="button" className="dv-secondary" onClick={async()=>{await thread.stop();setError("已停止接收本次研究；已发出的外部请求可能仍在结束中。");}}>停止研究</button>}
        </form>
        <p className="dv-note">不使用未知日期资料，不以缺失数字补齐估值。历史网页的当前版本不等同于历史归档。</p>
      </aside>
      <section className="dv-workspace">
        <div className="dv-heading">
          <div><div className="dv-kicker">VALUE RESEARCH</div><h2>{submitted ? `${activeScope.ticker} / ${activeScope.asOf}` : "先看证据，再形成判断。"}</h2></div>
          {report && !busy && <div className="dv-actions"><button onClick={()=>download("md")}>导出报告</button><button onClick={()=>download("json")}>导出证据 JSON</button></div>}
        </div>
        {error && <div role="alert" className="dv-error">{error}</div>}
        {submitted && <div className="dv-progress" aria-live="polite"><span className={busy?"dv-dot active":"dv-dot"}/><div><strong>{busy ? "研究中" : error ? "研究未完成" : report ? limited ? "研究结束 · 有限结论" : "研究完成" : "准备执行"}</strong><p>{events.at(-1) || "准备校验公司身份与参数"}</p></div><span>{events.length} 个节点更新</span></div>}
        {!submitted ? <div className="dv-empty">
          <div className="dv-number">01 / 03</div><h3>一份报告，一条证据链。</h3>
          <p>从截止日前已披露的 SEC 财报出发，核验新闻与政策的日期，把经营判断与估值假设分开。</p>
          <div className="dv-cards"><article><b>01</b><h4>锁定事实</h4><p>原始申报、会计概念、币种与期间。</p></article><article><b>02</b><h4>审查证据</h4><p>新闻、行业及政策，缺口明确呈现。</p></article><article><b>03</b><h4>复算情景</h4><p>用户假设、敏感性与来源一起导出。</p></article></div>
          <div className="dv-boundary">当前版本不含股价、安全边际、自动买卖结论或工业分部 DCF。默认截止日为 2025-03-01，可在左侧修改。</div>
        </div> : <>
          <div className="dv-metrics"><div><span>已取得财年</span><b>{financials.length}</b></div><div><span>日期核验来源</span><b>{evidence.length}</b></div><div><span>估值状态</span><b className="dv-metric-text">{values.valuation?.status==="calculated"?"已计算":values.valuation?.status==="blocked"?"不适用":"待校验"}</b></div></div>
          <nav className="dv-tabs">{[["report","研究报告"],["financials","财务数据"],["evidence","证据来源"],["activity","执行记录"]].map(([key,label])=><button aria-pressed={view===key} className={view===key?"selected":""} key={key} onClick={()=>setView(key)}>{label}</button>)}</nav>
          <div className="dv-content">
            {view==="report" && (busy ? <p className="dv-muted">正在收集与校验资料。完整结果将在流程结束后呈现。</p> : report ? <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{report}</ReactMarkdown> : <p className="dv-muted">报告尚未生成。{error ? "请检查错误并修改参数后重新研究。" : ""}</p>)}
            {view==="financials" && <div className="dv-table-wrap"><table><thead><tr><th>财年末 / 披露日</th><th>收入（百万美元）</th><th>经营现金流（百万美元）</th><th>稀释 EPS（美元）</th></tr></thead><tbody>{financials.map(row=><tr key={row.period_end}><td><a target="_blank" rel="noreferrer" href={row.url}>{row.period_end}</a><small>{row.filed}</small></td><td>{row.metrics.revenue ? (row.metrics.revenue.value/1e6).toLocaleString():"缺失"}</td><td>{row.metrics.operating_cash ? (row.metrics.operating_cash.value/1e6).toLocaleString():"缺失"}</td><td>{row.metrics.eps?.value ?? "缺失"}</td></tr>)}</tbody></table><p className="dv-note">完整概念、单位、来源 accession 及期间见导出的证据 JSON。</p></div>}
            {view==="evidence" && <div>{evidence.map(([id,item])=><article className="dv-evidence" key={id}><div className="dv-kicker">{item.category} · {item.published}</div><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a><p>{item.kind} · {item.date_basis}</p><details><summary>查看原文摘录与证据 ID</summary><small>{id}</small><pre>{item.excerpt}</pre></details></article>)}</div>}
            {view==="activity" && <ol className="dv-timeline">{events.map((event,index)=><li key={index}><span>{String(index+1).padStart(2,"0")}</span>{event}</li>)}</ol>}
          </div>
        </>}
      </section>
    </main>
  </div>;
}
