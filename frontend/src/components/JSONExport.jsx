import { Code2, Download } from "lucide-react";
export default function JSONExport({ data }) {
  const json = JSON.stringify(data, null, 2);
  const handleDownload = () => {
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "blotquant-analysis.json"; a.click(); URL.revokeObjectURL(url);
  };
  return (
    <div className="glass-card" style={{ overflow: 'hidden' }} data-testid="json-export">
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Code2 size={13} style={{ color: 'var(--text-muted)' }} />
          <span style={{ fontSize: 13, fontWeight: 600 }}>Raw JSON Output</span>
        </div>
        <button onClick={handleDownload} className="btn-outline" style={{ padding: '4px 12px', fontSize: 11 }}><Download size={11} /> Export</button>
      </div>
      <div className="code-block" style={{ border: 'none', borderRadius: 0 }}><pre>{json}</pre></div>
    </div>
  );
}
