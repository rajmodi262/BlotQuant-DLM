import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ErrorBar, Cell } from "recharts";

const COLORS = ["#00f2ff", "#a78bfa", "#ec4899", "#22c55e", "#f59e0b", "#60a5fa"];

const Tip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{ background: 'rgba(5,5,5,0.95)', border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', fontFamily: "'JetBrains Mono'", fontSize: 11 }}>
      <p style={{ color: '#fff', fontWeight: 600, marginBottom: 3 }}>{d.label}</p>
      <p style={{ color: 'var(--cyan)' }}>Intensity: {d.intensity?.toFixed(3)}</p>
      {d.ciLow != null && <p style={{ color: 'var(--text-muted)' }}>95% CI: [{d.ciLow?.toFixed(3)}, {d.ciHigh?.toFixed(3)}]</p>}
    </div>
  );
};

export default function IntensityChart({ bands, uncertainty }) {
  const data = (bands || []).map((b) => {
    const u = uncertainty?.find((x) => x.band_id === b.id);
    return {
      name: `L${b.lane}-B${b.id}`, label: b.label || `Band ${b.id}`,
      intensity: b.intensity,
      error: [u ? Math.max(0, b.intensity - u.ci_lower) : 0, u ? Math.max(0, u.ci_upper - b.intensity) : 0],
      ciLow: u?.ci_lower, ciHigh: u?.ci_upper,
    };
  });
  if (!data.length) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>No band data</div>;
  return (
    <div data-testid="intensity-chart">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <XAxis dataKey="name" tick={{ fontSize: 10, fontFamily: "'JetBrains Mono'", fill: 'var(--text-muted)' }} axisLine={{ stroke: 'rgba(255,255,255,0.06)' }} tickLine={false} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 10, fontFamily: "'JetBrains Mono'", fill: 'var(--text-dim)' }} axisLine={false} tickLine={false} width={36} />
          <Tooltip content={<Tip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
          <Bar dataKey="intensity" radius={[6, 6, 0, 0]} maxBarSize={36}>
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.7} />)}
            <ErrorBar dataKey="error" width={6} strokeWidth={1.5} stroke="rgba(255,255,255,0.2)" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
