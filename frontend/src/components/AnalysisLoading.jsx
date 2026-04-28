import { useState, useEffect } from "react";
import { Zap, ScanLine, BarChart3, ShieldCheck, FileOutput, Brain, Grid3x3, Eye, Waves, Activity } from "lucide-react";

const STEPS = [
  { icon: ScanLine, label: "Band Detection", color: "var(--cyan)" },
  { icon: BarChart3, label: "Densitometry", color: "#a78bfa" },
  { icon: Activity, label: "Monte Carlo CI", color: "#22c55e" },
  { icon: ShieldCheck, label: "Forensic Analysis", color: "#f59e0b" },
  { icon: Brain, label: "ResNet-18 Features", color: "#ec4899" },
  { icon: Grid3x3, label: "EfficientNet Patches", color: "var(--cyan)" },
  { icon: Eye, label: "Grad-CAM Attention", color: "#a78bfa" },
  { icon: Waves, label: "SSIM + Spectral", color: "#60a5fa" },
  { icon: FileOutput, label: "Building Report", color: "#22c55e" },
];

export default function AnalysisLoading() {
  const [step, setStep] = useState(0);
  const [pct, setPct] = useState(0);

  useEffect(() => {
    const si = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 2200);
    const pi = setInterval(() => setPct((p) => Math.min(p + 1, 95)), 100);
    return () => { clearInterval(si); clearInterval(pi); };
  }, []);

  return (
    <div data-testid="analysis-loading" style={{
      position: 'fixed', inset: 0, zIndex: 60,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      {/* 3D grid video background */}
      <video autoPlay muted loop playsInline style={{
        position: 'absolute', inset: 0, width: '100%', height: '100%',
        objectFit: 'cover', opacity: 0.7,
      }}>
        <source src="/assets/bg-processing.mp4" type="video/mp4" />
      </video>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'linear-gradient(180deg, rgba(5,5,5,0.3) 0%, rgba(5,5,5,0.5) 50%, rgba(5,5,5,0.4) 100%)',
      }} />

      <div style={{ maxWidth: 380, width: '100%', padding: '0 24px', textAlign: 'center', position: 'relative', zIndex: 2 }}>

        {/* Spinner ring */}
        <div style={{ position: 'relative', width: 80, height: 80, margin: '0 auto 24px' }}>
          <svg width="80" height="80" viewBox="0 0 80 80" className="animate-spin-slow">
            <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(0,242,255,0.08)" strokeWidth="2" />
            <circle cx="40" cy="40" r="36" fill="none" stroke="url(#grad)" strokeWidth="2.5"
              strokeDasharray="60 170" strokeLinecap="round" />
            <defs>
              <linearGradient id="grad"><stop stopColor="#00f2ff" /><stop offset="1" stopColor="#7c3aed" /></linearGradient>
            </defs>
          </svg>
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={22} style={{ color: 'var(--cyan)' }} />
          </div>
        </div>

        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4, fontFamily: "'Sora'" }}>Processing</h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>Running local DLM pipeline...</p>

        {/* Progress */}
        <div style={{ marginBottom: 24 }}>
          <div className="gauge-track">
            <div className="gauge-fill" style={{ width: `${pct}%`, background: 'var(--gradient)' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{STEPS[step]?.label}</span>
            <span style={{ fontSize: 12, color: 'var(--cyan)', fontFamily: "'JetBrains Mono'" }}>{pct}%</span>
          </div>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, textAlign: 'left' }}>
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const isDone = i < step;
            const isActive = i === step;
            return (
              <div key={i} className="glass-card" style={{
                padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10,
                borderColor: isActive ? 'rgba(0,242,255,0.15)' : isDone ? 'rgba(34,197,94,0.15)' : undefined,
                background: isActive ? 'rgba(0,242,255,0.03)' : isDone ? 'rgba(34,197,94,0.02)' : undefined,
              }}>
                <Icon size={14} style={{ color: isDone ? 'var(--green)' : isActive ? s.color : 'var(--text-dim)', flexShrink: 0 }} />
                <span style={{ fontSize: 12, flex: 1, color: isDone ? 'var(--text-secondary)' : isActive ? '#fff' : 'var(--text-muted)' }}>
                  {s.label}
                </span>
                {isDone && <span style={{ color: 'var(--green)', fontSize: 13 }}>✓</span>}
                {isActive && <div style={{ width: 12, height: 12, border: '2px solid var(--cyan)', borderTop: '2px solid transparent', borderRadius: '50%', animation: 'spin-slow 0.8s linear infinite' }} />}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
