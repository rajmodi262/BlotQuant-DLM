import { useState, useEffect } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import BandOverlay from "../components/BandOverlay";
import IntensityChart from "../components/IntensityChart";
import NormalizationCard from "../components/NormalizationCard";
import UncertaintyTable from "../components/UncertaintyTable";
import AuthenticityGauge from "../components/AuthenticityGauge";
import QualityDashboard from "../components/QualityDashboard";
import ExtendedFeatures from "../components/ExtendedFeatures";
import CombinedReport from "../components/CombinedReport";

import ForensicLens from "../components/ForensicLens";
import GridScanner from "../components/GridScanner";
import CompareSlider from "../components/CompareSlider";
import GradCamOverlay from "../components/GradCamOverlay";
import SpectralCard from "../components/SpectralCard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Loader2, FileText, Calendar, ScanLine, Layers, Shield, Brain, Activity, CheckCircle, Cpu, ClipboardCheck } from "lucide-react";

const API = `${import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"}/api`;

export default function ResultsPage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(location.state?.analysis || null);
  const [loading, setLoading] = useState(!location.state?.analysis);

  useEffect(() => {
    if (!analysis && id) {
      axios.get(`${API}/analyses/${id}`).then((r) => setAnalysis(r.data)).catch(() => navigate("/")).finally(() => setLoading(false));
    }
  }, [id, analysis, navigate]);

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
      <div className="animate-spin-slow">
        <svg width="40" height="40" viewBox="0 0 40 40">
          <circle cx="20" cy="20" r="16" fill="none" stroke="rgba(0,242,255,0.1)" strokeWidth="2" />
          <circle cx="20" cy="20" r="16" fill="none" stroke="url(#lgr)" strokeWidth="2.5" strokeDasharray="30 70" strokeLinecap="round" />
          <defs><linearGradient id="lgr"><stop stopColor="#00f2ff" /><stop offset="1" stopColor="#7c3aed" /></linearGradient></defs>
        </svg>
      </div>
    </div>
  );
  if (!analysis) return null;

  const { results, image_url, image_name, created_at } = analysis;
  const r = results || {};
  const base = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
  const imgUrl = image_url ? `${base}${image_url}` : null;
  const imgFilename = image_url?.split("/").pop();
  const elaUrl = imgFilename ? `${base}/api/ela/${imgFilename}` : null;
  const qPct = r.dl_quality?.quality_score != null ? Math.round(r.dl_quality.quality_score * 100) : null;

  // Count total models used
  const modelCount = [r.dl_quality?.method, r.patch_forensics?.method, r.gradcam?.method, r.spectral_analysis?.method]
    .filter(m => m && m !== 'fallback').length;

  const stats = [
    { icon: ScanLine, label: "Bands", value: r.bands?.length || 0, color: "var(--cyan)" },
    { icon: Layers, label: "Lanes", value: r.lanes?.length || 0, color: "#60a5fa" },
    { icon: Brain, label: "DL Quality", value: qPct != null ? `${qPct}%` : "—", color: qPct > 60 ? "var(--green)" : "var(--amber)" },
    { icon: Shield, label: "Authenticity", value: r.authenticity?.score != null ? `${Math.round(r.authenticity.score * 100)}%` : "—",
      color: r.authenticity?.score > 0.75 ? "var(--green)" : r.authenticity?.score > 0.45 ? "var(--amber)" : "var(--red)" },
    { icon: Cpu, label: "Models", value: modelCount, color: "#a78bfa" },
  ];

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      {/* Video background — machinery */}
      <div className="video-bg-wrapper">
        <video autoPlay muted loop playsInline>
          <source src="/assets/bg-results.mp4" type="video/mp4" />
        </video>
        <div className="video-bg-overlay" />
      </div>
      <div className="glow-bg" />
      <div style={{ position: 'relative', zIndex: 2 }}>
        <Header />

        <div className="container" style={{ paddingTop: 24, paddingBottom: 48 }}>

          {/* Title bar */}
          <div className="glass-card" style={{ padding: '14px 20px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 4 }} data-testid="results-title">
                Analysis <span className="gradient-text">Results</span>
              </h1>
              <div style={{ display: 'flex', gap: 14 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-muted)' }}>
                  <FileText size={11} /> {image_name}
                </span>
                {created_at && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-muted)' }}>
                    <Calendar size={11} /> {new Date(created_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <span className="badge badge-green"><CheckCircle size={10} /> Complete</span>
              <span className="badge badge-purple"><Cpu size={10} /> v3.0</span>
            </div>
          </div>

          {/* Stats row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 16 }}>
            {stats.map((s, i) => {
              const Icon = s.icon;
              return (
                <div key={i} className="stat-card">
                  <div className="stat-label"><Icon size={12} style={{ color: s.color }} /> {s.label}</div>
                  <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
                </div>
              );
            })}
          </div>

          {/* Main Tabs */}
          <Tabs defaultValue="detection" style={{ width: '100%' }}>
            <TabsList style={{ marginBottom: 12 }}>
              <TabsTrigger value="detection">Detection</TabsTrigger>
              <TabsTrigger value="forensics">Forensics</TabsTrigger>
              <TabsTrigger value="intensities">Intensities</TabsTrigger>
              <TabsTrigger value="deeplearning">Deep Learning</TabsTrigger>
              <TabsTrigger value="features">Features</TabsTrigger>
              <TabsTrigger value="report" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ClipboardCheck size={14} /> Report
              </TabsTrigger>
            </TabsList>

            {/* ═══ TAB: Detection ═══ */}
            <TabsContent value="detection">
              <div style={{ display: 'grid', gridTemplateColumns: '5fr 3fr', gap: 14 }}>
                <div className="glass-card" style={{ overflow: 'hidden' }}>
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Band Detection Overlay</span>
                    <span className="badge badge-cyan">{r.bands?.length || 0} bands</span>
                  </div>
                  <div style={{ padding: 14 }}>
                    <BandOverlay imageUrl={imgUrl} bands={r.bands} lanes={r.lanes} />
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <QualityDashboard dlQuality={r.dl_quality} extended={r.extended} />
                  <AuthenticityGauge data={r.authenticity} />
                  <NormalizationCard data={r.normalization} />
                </div>
              </div>
              {r.summary && (
                <div className="glass-card" style={{ padding: 16, marginTop: 12 }}>
                  <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>Summary</p>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.7 }} data-testid="analysis-summary">{r.summary}</p>
                </div>
              )}
            </TabsContent>

            {/* ═══ TAB: Forensics (NEW v3.0) ═══ */}
            <TabsContent value="forensics">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                {/* Forensic Lens */}
                <div className="glass-card" style={{ padding: 16 }}>
                  <ForensicLens originalUrl={imgUrl} elaUrl={elaUrl} />
                </div>
                {/* Grid Scanner */}
                <div className="glass-card" style={{ padding: 16 }}>
                  <GridScanner imageUrl={imgUrl} patchForensics={r.patch_forensics} />
                </div>
              </div>
              {/* Compare Slider */}
              <div className="glass-card" style={{ padding: 16, marginTop: 14 }}>
                <CompareSlider originalUrl={imgUrl} processedUrl={elaUrl} />
              </div>
            </TabsContent>

            {/* ═══ TAB: Intensities ═══ */}
            <TabsContent value="intensities">
              <div className="glass-card" style={{ padding: 20 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14 }}>
                  Band Intensities — <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>95% Confidence Intervals</span>
                </h3>
                <IntensityChart bands={r.bands} uncertainty={r.uncertainty} />
              </div>
              <div className="glass-card" style={{ padding: 20, marginTop: 14 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14 }}>
                  Monte Carlo Uncertainty — <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>30 Iterations</span>
                </h3>
                <UncertaintyTable bands={r.bands} uncertainty={r.uncertainty} />
              </div>
            </TabsContent>

            {/* ═══ TAB: Deep Learning (NEW v3.0) ═══ */}
            <TabsContent value="deeplearning">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <GradCamOverlay gradcam={r.gradcam} />
                <SpectralCard spectral={r.spectral_analysis} />
              </div>
              {r.ssim_analysis && (
                <div className="glass-card" style={{ padding: 18, marginTop: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      SSIM Band Comparison
                    </span>
                    <span className="badge badge-cyan" style={{ fontSize: 9 }}>Structural Similarity</span>
                  </div>
                  <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                    <div>
                      <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Avg Inter-Band</p>
                      <p style={{ fontSize: 20, fontWeight: 700, color: 'var(--cyan)', fontFamily: "'Sora'" }}>{r.ssim_analysis.avg_inter_ssim}</p>
                    </div>
                    <div>
                      <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Max Inter-Band</p>
                      <p style={{ fontSize: 20, fontWeight: 700, color: r.ssim_analysis.max_inter_ssim > 0.9 ? 'var(--amber)' : 'var(--text-secondary)', fontFamily: "'Sora'" }}>
                        {r.ssim_analysis.max_inter_ssim}
                      </p>
                    </div>
                    <div>
                      <p style={{ fontSize: 9, color: 'var(--text-muted)' }}>Avg Band→BG</p>
                      <p style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-secondary)', fontFamily: "'Sora'" }}>{r.ssim_analysis.avg_bg_ssim}</p>
                    </div>
                  </div>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>{r.ssim_analysis.interpretation}</p>
                </div>
              )}
            </TabsContent>

            {/* ═══ TAB: Features ═══ */}
            <TabsContent value="features">
              <ExtendedFeatures extended={r.extended} />
            </TabsContent>

            {/* ═══ TAB: Report (NEW) ═══ */}
            <TabsContent value="report">
              <CombinedReport analysis={analysis} />
            </TabsContent>

          </Tabs>
        </div>
      </div>
    </div>
  );
}
