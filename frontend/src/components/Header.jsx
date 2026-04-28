import { useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft, Plus, Zap } from "lucide-react";

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const isResults = location.pathname.startsWith("/results");

  return (
    <header className="app-header" data-testid="app-header">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', maxWidth: 1200, margin: '0 auto' }}>
        <button onClick={() => navigate("/")} data-testid="logo-button"
          style={{ background: 'none', border: 'none', display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
          <div style={{
            width: 32, height: 32, borderRadius: 10,
            background: 'var(--gradient)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px rgba(0,242,255,0.2)',
          }}>
            <Zap size={16} color="#050505" strokeWidth={2.5} />
          </div>
          <span style={{ fontFamily: "'Sora'", fontWeight: 700, fontSize: 16, letterSpacing: '-0.02em', color: '#fff' }}>
            BlotQuant
          </span>
          <span style={{
            fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 50,
            background: 'rgba(0,242,255,0.08)', color: 'var(--cyan)', border: '1px solid rgba(0,242,255,0.15)',
            fontFamily: "'JetBrains Mono'"
          }}>
            DLM
          </span>
        </button>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {isResults && (
            <button onClick={() => navigate("/")} className="btn-outline" data-testid="back-button">
              <ArrowLeft size={14} /> Back
            </button>
          )}
          <button onClick={() => navigate("/")} className="btn-gradient" data-testid="new-analysis-button">
            <Plus size={14} /> New Analysis
          </button>
        </div>
      </div>
    </header>
  );
}
