import { useState } from "react";
export default function BandOverlay({ imageUrl, bands, lanes }) {
  const [hovered, setHovered] = useState(null);
  if (!imageUrl) return null;
  return (
    <div data-testid="band-overlay" style={{ position: 'relative', borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border)' }}>
      <img src={imageUrl} alt="Western blot" style={{ width: '100%', display: 'block' }} />
      {lanes?.map((l) => (
        <div key={`l-${l.id}`} style={{ position: 'absolute', top: 0, height: '100%', left: `${l.position_x_pct}%`, borderLeft: '1px dashed rgba(255,255,255,0.1)' }}>
          <span style={{ position: 'absolute', top: 4, left: 4, fontSize: 9, color: 'var(--cyan)', background: 'rgba(5,5,5,0.8)', padding: '1px 6px', borderRadius: 50, fontFamily: "'JetBrains Mono'" }}>{l.label}</span>
        </div>
      ))}
      {bands?.map((b) => (
        <div key={`b-${b.id}`} data-testid={`band-box-${b.id}`}
          style={{
            position: 'absolute', cursor: 'crosshair',
            left: `${b.position_x_pct - b.width_pct / 2}%`, top: `${b.position_y_pct - b.height_pct / 2}%`,
            width: `${b.width_pct}%`, height: `${b.height_pct}%`,
            border: `1px solid ${hovered?.id === b.id ? 'rgba(0,242,255,0.6)' : 'rgba(0,242,255,0.25)'}`,
            background: hovered?.id === b.id ? 'rgba(0,242,255,0.1)' : 'rgba(0,242,255,0.03)',
            borderRadius: 4, transition: 'all 0.15s',
          }}
          onMouseEnter={() => setHovered(b)} onMouseLeave={() => setHovered(null)}
        >
          {hovered?.id === b.id && (
            <div style={{
              position: 'absolute', top: -34, left: '50%', transform: 'translateX(-50%)',
              background: 'rgba(5,5,5,0.95)', border: '1px solid var(--border)', borderRadius: 8,
              padding: '5px 10px', fontFamily: "'JetBrains Mono'", fontSize: 10, color: 'var(--text-secondary)',
              whiteSpace: 'nowrap', boxShadow: '0 4px 16px rgba(0,0,0,0.4)', zIndex: 20,
            }}>
              L{b.lane} · {b.molecular_weight_kda}kDa · I={b.intensity?.toFixed(2)}
            </div>
          )}
        </div>
      ))}
      <span className="badge badge-cyan" style={{ position: 'absolute', bottom: 8, right: 8 }}>{bands?.length || 0} bands</span>
    </div>
  );
}
