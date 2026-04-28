import { Microscope } from "lucide-react";
export default function NormalizationCard({ data }) {
  if (!data) return null;
  return (
    <div className="glass-card" style={{ padding: 18 }} data-testid="normalization-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <Microscope size={16} style={{ color: '#a78bfa' }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Normalization</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span className="badge badge-purple" style={{ textTransform: 'capitalize' }}>{(data.strategy || "").replace(/_/g, " ")}</span>
        {data.confidence != null && <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono'" }}>{Math.round(data.confidence * 100)}% conf</span>}
      </div>
      {data.description && <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>{data.description}</p>}
    </div>
  );
}
