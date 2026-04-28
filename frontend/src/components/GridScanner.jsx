import { useState } from "react";
import { Grid3x3, AlertTriangle, CheckCircle } from "lucide-react";

/**
 * GridScanner — 8×8 grid overlay on the image, color-coded by patch anomaly score.
 * Green = clean, Amber = moderate, Red = suspicious.
 * Hover shows patch details.
 */
export default function GridScanner({ imageUrl, patchForensics }) {
  const [hoveredCell, setHoveredCell] = useState(null);

  if (!patchForensics?.patch_scores || !imageUrl) return null;

  const { patch_scores, grid_size, max_score, mean_score, suspicious_count, method } = patchForensics;

  const getCellColor = (score) => {
    if (score >= 0.6) return "rgba(239,68,68,0.5)";
    if (score >= 0.4) return "rgba(245,158,11,0.4)";
    if (score >= 0.2) return "rgba(0,242,255,0.12)";
    return "rgba(34,197,94,0.08)";
  };

  const getCellBorder = (score) => {
    if (score >= 0.6) return "1px solid rgba(239,68,68,0.6)";
    if (score >= 0.4) return "1px solid rgba(245,158,11,0.4)";
    return "1px solid rgba(255,255,255,0.06)";
  };

  return (
    <div data-testid="grid-scanner">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Grid3x3 size={14} style={{ color: 'var(--cyan)' }} />
          <span style={{ fontSize: 13, fontWeight: 600 }}>Patch Forensics</span>
          <span className="badge badge-cyan" style={{ fontSize: 9 }}>{method}</span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {suspicious_count > 0 ? (
            <span className="badge badge-red"><AlertTriangle size={9} /> {suspicious_count} suspicious</span>
          ) : (
            <span className="badge badge-green"><CheckCircle size={9} /> Clean</span>
          )}
        </div>
      </div>

      <div style={{ position: 'relative', borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border)' }}>
        <img src={imageUrl} alt="Analysis" style={{ width: '100%', display: 'block' }} />

        {/* Grid overlay */}
        <div style={{
          position: 'absolute', inset: 0,
          display: 'grid',
          gridTemplateColumns: `repeat(${grid_size}, 1fr)`,
          gridTemplateRows: `repeat(${grid_size}, 1fr)`,
        }}>
          {patch_scores.flat().map((score, idx) => {
            const row = Math.floor(idx / grid_size);
            const col = idx % grid_size;
            const isHovered = hoveredCell?.row === row && hoveredCell?.col === col;

            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredCell({ row, col, score })}
                onMouseLeave={() => setHoveredCell(null)}
                style={{
                  background: getCellColor(score),
                  border: getCellBorder(score),
                  transition: 'all 0.15s',
                  cursor: 'crosshair',
                  position: 'relative',
                  ...(isHovered ? { background: 'rgba(0,242,255,0.2)', border: '1px solid var(--cyan)', zIndex: 10 } : {}),
                }}
              >
                {/* Score label on hover */}
                {isHovered && (
                  <div style={{
                    position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                    background: 'rgba(5,5,5,0.95)', border: '1px solid var(--border)', borderRadius: 8,
                    padding: '6px 10px', fontFamily: "'JetBrains Mono'", fontSize: 11,
                    whiteSpace: 'nowrap', boxShadow: '0 4px 16px rgba(0,0,0,0.5)', zIndex: 20,
                    color: score >= 0.6 ? 'var(--red)' : score >= 0.4 ? 'var(--amber)' : 'var(--green)',
                  }}>
                    [{row},{col}] → {(score * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono'" }}>
          Max: <span style={{ color: max_score >= 0.5 ? 'var(--red)' : 'var(--green)' }}>{(max_score * 100).toFixed(0)}%</span>
        </span>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono'" }}>
          Mean: {(mean_score * 100).toFixed(0)}%
        </span>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono'" }}>
          Grid: {grid_size}×{grid_size}
        </span>
      </div>
    </div>
  );
}
