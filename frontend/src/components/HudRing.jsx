/**
 * Animated HUD Ring — the centerpiece decoration.
 * Three concentric rotating SVG arcs with dashed strokes,
 * pulsing dots, and a central icon. This is what makes it look real.
 */
export default function HudRing({ size = 200, children }) {
  const c = size / 2;
  const r1 = c - 8;
  const r2 = c - 20;
  const r3 = c - 32;

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}
        style={{ position: 'absolute', top: 0, left: 0 }}>
        {/* Outer ring — slow rotate */}
        <circle cx={c} cy={c} r={r1}
          fill="none" stroke="rgba(79,195,247,0.12)" strokeWidth="1" />
        <circle cx={c} cy={c} r={r1}
          fill="none" stroke="rgba(79,195,247,0.5)" strokeWidth="1.5"
          strokeDasharray="8 6 20 6" strokeLinecap="round"
          className="hud-rotate"
          style={{ transformOrigin: `${c}px ${c}px` }} />

        {/* Middle ring — reverse rotate, dashed */}
        <circle cx={c} cy={c} r={r2}
          fill="none" stroke="rgba(79,195,247,0.08)" strokeWidth="1" />
        <circle cx={c} cy={c} r={r2}
          fill="none" stroke="rgba(79,195,247,0.35)" strokeWidth="1"
          strokeDasharray="4 12 8 12" strokeLinecap="round"
          className="hud-rotate-reverse"
          style={{ transformOrigin: `${c}px ${c}px` }} />

        {/* Inner ring — pulsing */}
        <circle cx={c} cy={c} r={r3}
          fill="none" stroke="rgba(79,195,247,0.15)" strokeWidth="0.5"
          className="hud-pulse" />

        {/* Tick marks on outer ring */}
        {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const x1t = c + (r1 + 2) * Math.cos(rad);
          const y1t = c + (r1 + 2) * Math.sin(rad);
          const x2t = c + (r1 + 6) * Math.cos(rad);
          const y2t = c + (r1 + 6) * Math.sin(rad);
          return (
            <line key={angle} x1={x1t} y1={y1t} x2={x2t} y2={y2t}
              stroke="rgba(79,195,247,0.25)" strokeWidth="1" />
          );
        })}

        {/* Cardinal dots */}
        {[0, 90, 180, 270].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const dx = c + r2 * Math.cos(rad);
          const dy = c + r2 * Math.sin(rad);
          return (
            <circle key={`dot-${angle}`} cx={dx} cy={dy} r="2"
              fill="rgba(79,195,247,0.6)" className="hud-pulse" />
          );
        })}

        {/* Cross-hairs */}
        <line x1={c - 8} y1={c} x2={c - 3} y2={c} stroke="rgba(79,195,247,0.3)" strokeWidth="0.5" />
        <line x1={c + 3} y1={c} x2={c + 8} y2={c} stroke="rgba(79,195,247,0.3)" strokeWidth="0.5" />
        <line x1={c} y1={c - 8} x2={c} y2={c - 3} stroke="rgba(79,195,247,0.3)" strokeWidth="0.5" />
        <line x1={c} y1={c + 3} x2={c} y2={c + 8} stroke="rgba(79,195,247,0.3)" strokeWidth="0.5" />
      </svg>

      {/* Center content */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {children}
      </div>
    </div>
  );
}
