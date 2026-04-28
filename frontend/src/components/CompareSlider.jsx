import { useState, useRef, useCallback } from "react";
import { SplitSquareHorizontal } from "lucide-react";

/**
 * CompareSlider — Drag a vertical line to compare original vs processed image.
 */
export default function CompareSlider({ originalUrl, processedUrl, labelLeft = "Original", labelRight = "ELA Enhanced" }) {
  const containerRef = useRef(null);
  const [position, setPosition] = useState(50);
  const [dragging, setDragging] = useState(false);

  const handleMove = useCallback((e) => {
    if (!dragging) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    setPosition(Math.max(2, Math.min(98, x)));
  }, [dragging]);

  const handleTouchMove = useCallback((e) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = ((e.touches[0].clientX - rect.left) / rect.width) * 100;
    setPosition(Math.max(2, Math.min(98, x)));
  }, []);

  if (!originalUrl || !processedUrl) return null;

  return (
    <div data-testid="compare-slider">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <SplitSquareHorizontal size={14} style={{ color: '#a78bfa' }} />
        <span style={{ fontSize: 13, fontWeight: 600 }}>Before / After Comparison</span>
      </div>

      <div
        ref={containerRef}
        onMouseMove={handleMove}
        onMouseUp={() => setDragging(false)}
        onMouseLeave={() => setDragging(false)}
        onTouchMove={handleTouchMove}
        onTouchEnd={() => setDragging(false)}
        style={{
          position: 'relative', borderRadius: 12, overflow: 'hidden',
          border: '1px solid var(--border)', cursor: dragging ? 'col-resize' : 'default',
          userSelect: 'none',
        }}
      >
        {/* Right image (processed/ELA) — full width, behind */}
        <img src={processedUrl} alt={labelRight} style={{ width: '100%', display: 'block' }} />

        {/* Left image (original) — clipped by slider position */}
        <div style={{
          position: 'absolute', inset: 0, overflow: 'hidden',
          width: `${position}%`,
        }}>
          <img src={originalUrl} alt={labelLeft} style={{ width: `${100 / position * 100}%`, maxWidth: 'none', display: 'block' }} />
        </div>

        {/* Slider handle */}
        <div
          onMouseDown={() => setDragging(true)}
          onTouchStart={() => setDragging(true)}
          style={{
            position: 'absolute', top: 0, bottom: 0, left: `${position}%`,
            width: 3, background: 'var(--cyan)', cursor: 'col-resize', zIndex: 10,
            boxShadow: '0 0 12px rgba(0,242,255,0.4)',
            transform: 'translateX(-50%)',
          }}
        >
          {/* Handle grip */}
          <div style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 32, height: 32, borderRadius: '50%',
            background: 'rgba(5,5,5,0.9)', border: '2px solid var(--cyan)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px rgba(0,242,255,0.3)',
          }}>
            <SplitSquareHorizontal size={14} style={{ color: 'var(--cyan)' }} />
          </div>
        </div>

        {/* Labels */}
        <span style={{
          position: 'absolute', top: 8, left: 8, fontSize: 10, fontWeight: 600,
          padding: '3px 8px', borderRadius: 50,
          background: 'rgba(5,5,5,0.8)', color: 'var(--text-secondary)',
          fontFamily: "'JetBrains Mono'", backdropFilter: 'blur(8px)',
        }}>{labelLeft}</span>
        <span style={{
          position: 'absolute', top: 8, right: 8, fontSize: 10, fontWeight: 600,
          padding: '3px 8px', borderRadius: 50,
          background: 'rgba(5,5,5,0.8)', color: 'var(--cyan)',
          fontFamily: "'JetBrains Mono'", backdropFilter: 'blur(8px)',
        }}>{labelRight}</span>
      </div>
    </div>
  );
}
