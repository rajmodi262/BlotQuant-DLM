import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";

const CFG = {
  likely_authentic: { icon: ShieldCheck, label: "Authentic", color: "var(--green)", cls: "badge-green" },
  possibly_manipulated: { icon: ShieldAlert, label: "Suspicious", color: "var(--amber)", cls: "badge-amber" },
  likely_manipulated: { icon: ShieldX, label: "Manipulated", color: "var(--red)", cls: "badge-red" },
};

export default function AuthenticityGauge({ data }) {
  if (!data) return null;
  const c = CFG[data.classification] || CFG.likely_authentic;
  const Icon = c.icon;
  const pct = Math.round((data.score || 0) * 100);

  return (
    <div className="glass-card" style={{ padding: 18 }} data-testid="authenticity-gauge">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Icon size={16} style={{ color: c.color }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Authenticity
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span className={`badge ${c.cls}`}>{c.label}</span>
        <span style={{ fontSize: 28, fontWeight: 700, color: c.color, fontFamily: "'Sora'" }}>{pct}%</span>
      </div>
      <div className="gauge-track">
        <div className="gauge-fill" style={{ width: `${pct}%`, background: c.color }} />
      </div>
      {data.findings?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {data.findings.map((f, i) => (
            <p key={i} style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6, paddingLeft: 12, borderLeft: `2px solid ${c.color}20`, marginBottom: 4 }}>
              {f}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
