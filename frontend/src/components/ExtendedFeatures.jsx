import { Activity, Gauge, Maximize2, Sun, Layers, ArrowRightLeft, FlaskConical } from "lucide-react";
const FEATURES = {
  snr: { label: "Signal/Noise", icon: Activity, key: "average" },
  band_sharpness: { label: "Sharpness", icon: Maximize2, key: "average" },
  saturation: { label: "Saturation", icon: Sun, key: "status" },
  dynamic_range: { label: "Dynamic Range", icon: Gauge, key: "range_pct", suffix: "%" },
  band_symmetry: { label: "Symmetry", icon: ArrowRightLeft, key: "average" },
  loading_evenness: { label: "Loading", icon: Layers, key: "evenness_score" },
  transfer_efficiency: { label: "Transfer", icon: FlaskConical, key: "score" },
  background_gradient: { label: "Gradient", icon: Layers, key: "status" },
};
const COLOR = {
  excellent: "var(--green)", good: "var(--green)", sharp: "var(--green)", uniform: "var(--green)", symmetric: "var(--green)", even: "var(--green)", efficient: "var(--green)",
  moderate: "var(--amber)", moderate_clipping: "var(--amber)", mild_gradient: "var(--amber)",
  poor: "var(--red)", blurry: "var(--red)", uneven: "var(--red)", asymmetric: "var(--red)", severe_clipping: "var(--red)", significant_gradient: "var(--red)",
};
export default function ExtendedFeatures({ extended }) {
  if (!extended) return null;
  return (
    <div className="glass-card" style={{ padding: 20 }} data-testid="extended-features">
      <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14 }}>
        Extended <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>Analysis Features</span>
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
        {Object.entries(FEATURES).map(([fk, cfg]) => {
          const d = extended[fk];
          if (!d) return null;
          const Icon = cfg.icon;
          const val = d[cfg.key];
          const status = d.status;
          const color = COLOR[status] || "var(--cyan)";
          const display = typeof val === "number" ? `${val.toFixed?.(2) ?? val}${cfg.suffix || ""}` : val || "—";
          return (
            <div key={fk} className="glass-card" style={{ padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 32, height: 32, borderRadius: 10, background: `${color}12`, border: `1px solid ${color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Icon size={14} style={{ color }} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>{cfg.label}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color, fontFamily: "'JetBrains Mono'" }}>{display}</span>
                  {status && <span className={`badge ${color === 'var(--green)' ? 'badge-green' : color === 'var(--amber)' ? 'badge-amber' : 'badge-red'}`} style={{ fontSize: 8 }}>{status.replace(/_/g, " ")}</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {extended.image_stats && (
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--border)', display: 'flex', gap: 16 }}>
          {[`${extended.image_stats.width}×${extended.image_stats.height}px`, `μ=${extended.image_stats.mean_intensity}`, `σ=${extended.image_stats.std_intensity}`].map((t, i) => (
            <span key={i} style={{ fontSize: 10, color: 'var(--text-dim)', fontFamily: "'JetBrains Mono'" }}>{t}</span>
          ))}
        </div>
      )}
    </div>
  );
}
