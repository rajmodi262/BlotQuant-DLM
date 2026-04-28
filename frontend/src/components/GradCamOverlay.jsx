import { Brain, Crosshair } from "lucide-react";

/**
 * GradCamOverlay — Displays the Grad-CAM attention heatmap as a color grid overlay.
 */
export default function GradCamOverlay({ gradcam }) {
  if (!gradcam?.heatmap) return null;
  const { heatmap, peak_attention, mean_attention, attention_spread, focus_region, method } = gradcam;
  const rows = heatmap.length;
  const cols = heatmap[0]?.length || 0;

  const getColor = (val) => {
    // Blue → Cyan → Yellow → Red gradient
    if (val < 0.25) return `rgba(59,130,246,${val * 2})`;
    if (val < 0.5) return `rgba(0,242,255,${0.3 + val * 0.5})`;
    if (val < 0.75) return `rgba(245,158,11,${0.3 + val * 0.5})`;
    return `rgba(239,68,68,${0.4 + val * 0.5})`;
  };

  return (
    <div className="glass-card" style={{ padding: 18 }} data-testid="gradcam-overlay">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Brain size={16} style={{ color: '#ec4899' }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Grad-CAM Attention
        </span>
        <span className="badge badge-purple" style={{ fontSize: 9 }}>{method}</span>
      </div>

      {/* Heatmap grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gridTemplateRows: `repeat(${rows}, 1fr)`,
        gap: 2, borderRadius: 8, overflow: 'hidden',
        border: '1px solid var(--border)',
        marginBottom: 12,
      }}>
        {heatmap.flat().map((val, idx) => (
          <div key={idx} style={{
            aspectRatio: '1', background: getColor(val),
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s', cursor: 'default',
          }}
            title={`Attention: ${(val * 100).toFixed(0)}%`}
          >
            {val > 0.6 && <span style={{ fontSize: 8, color: '#fff', fontFamily: "'JetBrains Mono'", fontWeight: 600 }}>
              {(val * 100).toFixed(0)}
            </span>}
          </div>
        ))}
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Peak</p>
          <p style={{ fontSize: 14, fontWeight: 600, color: '#ec4899', fontFamily: "'JetBrains Mono'" }}>{(peak_attention * 100).toFixed(0)}%</p>
        </div>
        <div>
          <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Mean</p>
          <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', fontFamily: "'JetBrains Mono'" }}>{(mean_attention * 100).toFixed(0)}%</p>
        </div>
        <div>
          <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Spread</p>
          <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--cyan)', fontFamily: "'JetBrains Mono'" }}>{(attention_spread * 100).toFixed(0)}%</p>
        </div>
        <div>
          <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Focus</p>
          <p style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Crosshair size={10} /> {focus_region?.replace(/_/g, ' ')}
          </p>
        </div>
      </div>
    </div>
  );
}
