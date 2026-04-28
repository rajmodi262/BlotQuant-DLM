import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import Header from "../components/Header";
import UploadZone from "../components/UploadZone";
import AnalysisLoading from "../components/AnalysisLoading";
import SampleGallery from "../components/SampleGallery";
import { ScanLine, BarChart3, Shield, Activity, Brain, Database, Zap, ArrowRight, Grid3x3, Eye, Waves, GitCompare } from "lucide-react";

const API = `${import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"}/api`;

const MODULES = [
  { icon: ScanLine, title: "Band Detection", desc: "OpenCV adaptive thresholding + contour extraction", color: "var(--cyan)" },
  { icon: BarChart3, title: "Densitometry", desc: "Background-corrected pixel intensity quantification", color: "#a78bfa" },
  { icon: Activity, title: "Monte Carlo CI", desc: "30-iteration simulation for 95% confidence intervals", color: "#22c55e" },
  { icon: Shield, title: "Forensic Scoring", desc: "ELA, noise profiling, ORB copy-move detection", color: "#f59e0b" },
  { icon: Brain, title: "ResNet-18 DL", desc: "Pretrained CNN features + image quality scoring", color: "#ec4899" },
  { icon: Grid3x3, title: "EfficientNet Patches", desc: "8×8 grid patch-based anomaly heatmap generation", color: "#06b6d4" },
  { icon: Eye, title: "Grad-CAM", desc: "Explainable AI — attention maps showing model focus", color: "#f472b6" },
  { icon: GitCompare, title: "SSIM Analysis", desc: "Structural similarity between bands and background", color: "#60a5fa" },
  { icon: Waves, title: "Spectral FFT", desc: "Frequency domain analysis for artifact detection", color: "#818cf8" },
  { icon: Database, title: "Extended Metrics", desc: "SNR, sharpness, symmetry, saturation analysis", color: "#34d399" },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = useCallback(async (file) => {
    setAnalyzing(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await axios.post(`${API}/analyze`, fd, { headers: { "Content-Type": "multipart/form-data" }, timeout: 120000 });
      toast.success("Analysis complete");
      navigate(`/results/${res.data.id}`, { state: { analysis: res.data } });
    } catch (err) {
      toast.error(err.response?.data?.detail || "Analysis failed");
    } finally { setAnalyzing(false); }
  }, [navigate]);

  const handleSample = useCallback(async (id) => {
    setAnalyzing(true);
    try {
      const res = await axios.post(`${API}/analyze-sample/${id}`, {}, { timeout: 120000 });
      toast.success("Analysis complete");
      navigate(`/results/${res.data.id}`, { state: { analysis: res.data } });
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed");
    } finally { setAnalyzing(false); }
  }, [navigate]);

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      {/* Video background */}
      <div className="video-bg-wrapper">
        <video autoPlay muted loop playsInline>
          <source src="/assets/bg-video.mp4" type="video/mp4" />
        </video>
        <div className="video-bg-overlay" />
      </div>
      <div className="glow-bg" />
      <div style={{ position: 'relative', zIndex: 2 }}>
        <Header />
        {analyzing && <AnalysisLoading />}

        <div className="container" style={{ paddingTop: 60, paddingBottom: 80 }}>

          {/* ═══ HERO ═══ */}
          <div style={{ textAlign: 'center', marginBottom: 56, maxWidth: 680, marginLeft: 'auto', marginRight: 'auto' }}>
            <div className="animate-fade-up" style={{ marginBottom: 16 }}>
              <span className="badge badge-cyan" style={{ fontSize: 11 }}>
                <Zap size={10} /> Powered by ResNet-18 + OpenCV
              </span>
            </div>

            <h1 className="animate-fade-up" style={{
              fontSize: 56, fontWeight: 800, lineHeight: 1.1, letterSpacing: '-0.04em',
              marginBottom: 20,
            }}>
              Western Blot<br />
              <span className="gradient-text">Deep Learning</span> Analysis
            </h1>

            <p className="animate-fade-up" style={{
              fontSize: 17, color: 'var(--text-secondary)', lineHeight: 1.7,
              maxWidth: 520, margin: '0 auto 32px',
            }}>
              Upload a blot image. Our local pipeline runs band detection, densitometry,
              Monte Carlo uncertainty, forensics, and CNN feature extraction — entirely on your device.
            </p>

            {/* Pipeline flow pills */}
            <div className="animate-fade-up" style={{
              display: 'flex', justifyContent: 'center', flexWrap: 'wrap',
              gap: 6, marginBottom: 40, alignItems: 'center',
            }}>
              {["Upload", "Detect", "Quantify", "MC CI", "Forensics", "ResNet", "EfficientNet", "Grad-CAM", "SSIM+FFT", "Report"].map((s, i) => (
                <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{
                    padding: '4px 12px', borderRadius: 50, fontSize: 11, fontWeight: 500,
                    background: i === 0 ? 'rgba(0,242,255,0.1)' : 'rgba(255,255,255,0.04)',
                    color: i === 0 ? 'var(--cyan)' : 'var(--text-muted)',
                    border: `1px solid ${i === 0 ? 'rgba(0,242,255,0.2)' : 'rgba(255,255,255,0.06)'}`,
                  }}>
                    {s}
                  </span>
                  {i < 9 && <ArrowRight size={12} style={{ color: 'var(--text-dim)' }} />}
                </div>
              ))}
            </div>
          </div>

          {/* ═══ UPLOAD + SAMPLES ═══ */}
          <div style={{ maxWidth: 540, margin: '0 auto 28px' }}>
            <UploadZone onFileSelect={handleAnalyze} disabled={analyzing} />
          </div>
          <div style={{ maxWidth: 720, margin: '0 auto 72px' }}>
            <SampleGallery onAnalyzeSample={handleSample} disabled={analyzing} />
          </div>

          {/* ═══ PIPELINE MODULES ═══ */}
          <div>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <h2 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 8 }}>
                <span className="gradient-text">Ten-Stage</span> Pipeline
              </h2>
              <p style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 460, margin: '0 auto' }}>
                Every blot passes through all ten analysis modules — powered by ResNet-18 + EfficientNet-B0.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
              {MODULES.map((m, i) => {
                const Icon = m.icon;
                return (
                  <div key={i} className="glass-card-glow" style={{ padding: '22px 20px' }}>
                    <div style={{
                      width: 40, height: 40, borderRadius: 12,
                      background: `${m.color}10`, border: `1px solid ${m.color}20`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      marginBottom: 14,
                    }}>
                      <Icon size={18} style={{ color: m.color }} />
                    </div>
                    <h3 style={{ fontSize: 15, fontWeight: 600, color: '#fff', marginBottom: 4, letterSpacing: '-0.01em' }}>
                      {m.title}
                    </h3>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>{m.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ═══ FOOTER ═══ */}
          <div style={{
            marginTop: 80, paddingTop: 24,
            borderTop: '1px solid var(--border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
              BlotQuant DLM © {new Date().getFullYear()} — Local CV + Deep Learning
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-dim)', fontFamily: "'JetBrains Mono'" }}>
              ResNet-18 · OpenCV · NumPy · SciPy
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
