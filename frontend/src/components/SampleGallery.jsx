import { useState, useEffect } from "react";
import axios from "axios";
import { Zap } from "lucide-react";

const API = `${import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"}/api`;
const BASE = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const FALLBACK_SAMPLES = [
  {
    id: "sample-1",
    name: "Multi-lane Western Blot",
    filename: "sample-blot.png",
    thumbnail: "/api/images/sample-blot.png",
    description: "Multi-lane blot with protein markers (10-35 kDa)",
  },
  {
    id: "sample-2",
    name: "PVDF Membrane Blot",
    filename: "sample-blot-2.png",
    thumbnail: "/api/images/sample-blot-2.png",
    description: "4-lane PVDF membrane with chemiluminescent bands",
  },
  {
    id: "sample-3",
    name: "Overexposed Blot",
    filename: "sample-blot-3.png",
    thumbnail: "/api/images/sample-blot-3.png",
    description: "Overexposed blot with saturated bands — tests forensics",
  }
];

export default function SampleGallery({ onAnalyzeSample, disabled }) {
  const [samples, setSamples] = useState([]);
  
  useEffect(() => { 
    axios.get(`${API}/samples`)
      .then((r) => setSamples(r.data))
      .catch(() => {
        // Fallback to static sample metadata if backend is offline
        setSamples(FALLBACK_SAMPLES);
      }); 
  }, []);
  
  if (!samples.length) return null;

  return (
    <div data-testid="sample-gallery">
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, textAlign: 'center' }}>
        Or try a sample image
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(samples.length, 3)}, 1fr)`, gap: 12 }}>
        {samples.map((s) => (
          <button key={s.id} data-testid={`sample-${s.id}`} disabled={disabled}
            onClick={() => onAnalyzeSample(s.id)}
            style={{ all: 'unset', cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1 }}>
            <div className="glass-card-glow" style={{ overflow: 'hidden' }}>
              <div style={{ height: 130, overflow: 'hidden', position: 'relative' }}>
                {/* Fallback to local assets folder if the backend server is completely unavailable to serve the /api/images/ */}
                <img src={s.thumbnail.includes('/api/images/') ? `/assets/${s.filename}` : `${BASE}${s.thumbnail}`} alt={s.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.75, transition: 'all 0.3s' }}
                  onMouseEnter={(e) => { e.target.style.opacity = 1; e.target.style.transform = 'scale(1.03)'; }}
                  onMouseLeave={(e) => { e.target.style.opacity = 0.75; e.target.style.transform = 'scale(1)'; }} 
                  onError={(e) => {
                    // Try alternative path if first fails
                    if (!e.target.src.includes('/assets/')) {
                      e.target.src = `/assets/${s.filename}`;
                    }
                  }}
                />
                <div style={{ position: 'absolute', top: 8, right: 8 }}>
                  <div className="badge badge-cyan" style={{ fontSize: 9, backdropFilter: 'blur(8px)' }}>
                    <Zap size={8} /> Analyze
                  </div>
                </div>
              </div>
              <div style={{ padding: '12px 14px' }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 3 }}>{s.name}</p>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
