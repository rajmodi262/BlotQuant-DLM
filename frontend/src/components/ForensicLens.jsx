import { useState, useRef, useCallback } from "react";
import { Eye } from "lucide-react";

/**
 * ForensicLens — Hover to reveal ELA/processed image through a circular lens.
 * Outside lens = original image | Inside lens = forensic (ELA) image.
 */
export default function ForensicLens({ originalUrl, elaUrl }) {
  const containerRef = useRef(null);
  const [pos, setPos] = useState({ x: 50, y: 50 });
  const [active, setActive] = useState(false);
  const RADIUS = 90;

  const handleMove = useCallback((e) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setPos({ x: Math.max(0, Math.min(100, x)), y: Math.max(0, Math.min(100, y)) });
  }, []);

  if (!originalUrl || !elaUrl) return null;

  return (
    <div data-testid="forensic-lens">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Eye size={14} style={{ color: 'var(--cyan)' }} />
          <span style={{ fontSize: 13, fontWeight: 600 }}>Forensic Lens</span>
          <span className="badge badge-purple" style={{ fontSize: 9 }}>ELA</span>
        </div>
        <button
          className="btn-outline"
          style={{ padding: '4px 12px', fontSize: 11 }}
          onClick={() => setActive(!active)}
        >
          {active ? "Disable Lens" : "Enable Lens"}
        </button>
      </div>

      <div
        ref={containerRef}
        onMouseMove={active ? handleMove : undefined}
        style={{
          position: 'relative', borderRadius: 12, overflow: 'hidden',
          border: '1px solid var(--border)', cursor: active ? 'none' : 'default',
        }}
      >
        {/* Original image (always visible) */}
        <img src={originalUrl} alt="Original" style={{ width: '100%', display: 'block' }} />

        {/* ELA image (revealed through circular clip) */}
        {active && (
          <div style={{
            position: 'absolute', inset: 0,
            clipPath: `circle(${RADIUS}px at ${pos.x}% ${pos.y}%)`,
            transition: 'clip-path 0.05s ease-out',
          }}>
            <img src={elaUrl} alt="ELA Analysis" style={{ width: '100%', display: 'block' }} />
            {/* Lens ring */}
            <div style={{
              position: 'absolute',
              left: `calc(${pos.x}% - ${RADIUS}px)`, top: `calc(${pos.y}% - ${RADIUS}px)`,
              width: RADIUS * 2, height: RADIUS * 2,
              border: '2px solid var(--cyan)', borderRadius: '50%',
              boxShadow: '0 0 20px rgba(0,242,255,0.3), inset 0 0 20px rgba(0,242,255,0.05)',
              pointerEvents: 'none',
            }} />
          </div>
        )}

        {/* Crosshair */}
        {active && (
          <>
            <div style={{
              position: 'absolute', left: `${pos.x}%`, top: 0,
              width: 1, height: '100%', background: 'rgba(0,242,255,0.15)',
              pointerEvents: 'none',
            }} />
            <div style={{
              position: 'absolute', top: `${pos.y}%`, left: 0,
              height: 1, width: '100%', background: 'rgba(0,242,255,0.15)',
              pointerEvents: 'none',
            }} />
          </>
        )}

        {!active && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(5,5,5,0.3)', opacity: 0, transition: 'opacity 0.2s',
          }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = 1}
            onMouseLeave={(e) => e.currentTarget.style.opacity = 0}
          >
            <span style={{ fontSize: 13, color: '#fff', fontWeight: 500 }}>Click "Enable Lens" to scan</span>
          </div>
        )}
      </div>

      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.4 }}>
        Move cursor to reveal ELA (Error Level Analysis) — manipulated regions show different error levels.
      </p>
    </div>
  );
}
