import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { Brain } from "lucide-react";

export default function QualityDashboard({ dlQuality, extended }) {
  if (!dlQuality && !extended) return null;

  const radarData = [];
  if (extended?.snr?.average != null) radarData.push({ m: "SNR", v: Math.min(10, extended.snr.average) / 10 });
  if (extended?.band_sharpness?.average != null) radarData.push({ m: "Sharp", v: Math.min(500, extended.band_sharpness.average) / 500 });
  if (extended?.saturation) radarData.push({ m: "Exposure", v: Math.max(0, 1 - (extended.saturation.black_pct + extended.saturation.white_pct) / 100) });
  if (extended?.dynamic_range?.range_pct != null) radarData.push({ m: "Range", v: extended.dynamic_range.range_pct / 100 });
  if (extended?.band_symmetry?.average != null) radarData.push({ m: "Symmetry", v: extended.band_symmetry.average });
  if (extended?.loading_evenness?.evenness_score != null) radarData.push({ m: "Loading", v: extended.loading_evenness.evenness_score });

  const qPct = dlQuality?.quality_score != null ? Math.round(dlQuality.quality_score * 100) : null;
  const isResNet = dlQuality?.method === "resnet18_feature_analysis";

  return (
    <div className="glass-card" style={{ padding: 18 }} data-testid="quality-dashboard">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Brain size={16} style={{ color: '#a78bfa' }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          DL Quality
        </span>
        <span className={isResNet ? "badge badge-purple" : "badge badge-cyan"} style={{ fontSize: 9 }}>
          {isResNet ? "ResNet-18" : "OpenCV"}
        </span>
      </div>

      {qPct != null && (
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 14 }}>
          <span className="gradient-text" style={{ fontSize: 32, fontWeight: 700, fontFamily: "'Sora'" }}>{qPct}%</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>quality score</span>
        </div>
      )}

      {radarData.length >= 3 && (
        <ResponsiveContainer width="100%" height={180}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="rgba(255,255,255,0.04)" />
            <PolarAngleAxis dataKey="m" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
            <PolarRadiusAxis angle={90} domain={[0, 1]} tick={false} axisLine={false} />
            <Radar dataKey="v" stroke="url(#radarGrad)" fill="url(#radarGrad)" fillOpacity={0.08} strokeWidth={1.5} />
            <defs>
              <linearGradient id="radarGrad"><stop stopColor="#00f2ff" /><stop offset="1" stopColor="#7c3aed" /></linearGradient>
            </defs>
          </RadarChart>
        </ResponsiveContainer>
      )}

      {dlQuality?.metrics && (
        <div style={{ marginTop: 8 }}>
          {Object.entries(dlQuality.metrics).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}</span>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontFamily: "'JetBrains Mono'" }}>{v}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
