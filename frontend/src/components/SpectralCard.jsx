import { Radio, Waves } from "lucide-react";

/**
 * SpectralCard — Displays FFT spectral analysis results with a power spectrum grid.
 */
export default function SpectralCard({ spectral }) {
  if (!spectral?.power_spectrum) return null;
  const { power_spectrum, has_periodic_noise, periodic_peak_count, dominant_frequency,
          spectral_entropy, radial_power, method } = spectral;
  const size = power_spectrum.length;

  return (
    <div className="glass-card" style={{ padding: 18 }} data-testid="spectral-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Waves size={16} style={{ color: '#60a5fa' }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Spectral Analysis
        </span>
        <span className="badge badge-cyan" style={{ fontSize: 9 }}>FFT</span>
      </div>

      {/* Power spectrum grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: `repeat(${size}, 1fr)`,
        gap: 1, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)',
        marginBottom: 12,
      }}>
        {power_spectrum.flat().map((val, idx) => (
          <div key={idx} style={{
            aspectRatio: '1',
            background: `rgba(0,242,255,${val * 0.8})`,
          }} title={`Power: ${val.toFixed(3)}`} />
        ))}
      </div>

      {/* Periodic noise alert */}
      {has_periodic_noise && (
        <div style={{
          padding: '8px 12px', borderRadius: 8, marginBottom: 12,
          background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <Radio size={12} style={{ color: 'var(--amber)' }} />
          <span style={{ fontSize: 11, color: 'var(--amber)' }}>
            Periodic noise detected ({periodic_peak_count} peaks) — possible scanner artifacts
          </span>
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Entropy</p>
          <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--cyan)', fontFamily: "'JetBrains Mono'" }}>{spectral_entropy}</p>
        </div>
        <div>
          <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Dom. Freq</p>
          <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', fontFamily: "'JetBrains Mono'" }}>{dominant_frequency}</p>
        </div>
        <div>
          <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Noise</p>
          <p style={{ fontSize: 12, fontWeight: 500 }}>
            <span className={has_periodic_noise ? "badge badge-amber" : "badge badge-green"} style={{ fontSize: 9 }}>
              {has_periodic_noise ? "Detected" : "Clean"}
            </span>
          </p>
        </div>
      </div>

      {/* Radial power distribution */}
      {radial_power?.length > 0 && (
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
          <p style={{ fontSize: 9, color: 'var(--text-muted)', marginBottom: 6 }}>Radial Power (Low → High freq)</p>
          <div style={{ display: 'flex', gap: 4, alignItems: 'flex-end', height: 40 }}>
            {radial_power.map((p, i) => (
              <div key={i} style={{
                flex: 1, borderRadius: '4px 4px 0 0',
                height: `${Math.max(8, p * 100)}%`,
                background: `rgba(0,242,255,${0.3 + p * 0.5})`,
                transition: 'height 0.3s',
              }} title={`Band ${i + 1}: ${p}`} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
