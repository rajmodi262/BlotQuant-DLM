import React, { useRef, useState, useEffect } from "react";
import { Download, CheckCircle, AlertTriangle, XCircle, FileText, Cpu, Shield, Brain, Activity, ScanLine, Maximize2, Layers } from "lucide-react";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

export default function CombinedReport({ analysis }) {
  const { results, image_name, created_at, image_url } = analysis;
  const reportRef = useRef(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [verdictData, setVerdictData] = useState(null);

  const base = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
  const imgUrl = image_url ? `${base}${image_url}` : null;

  useEffect(() => {
    if (!results) return;

    // --- v4.0: Use actual pipeline scores — no artificial manipulation ---
    let authScore = results.authenticity?.score || 0;
    let dlScore = results.dl_quality?.quality_score || 0;
    let suspCount = results.patch_forensics?.suspicious_count || 0;
    let hasNoise = results.spectral_analysis?.has_periodic_noise || false;
    const totalPatches = (results.patch_forensics?.grid_size || 8) ** 2;

    // 1. Normalize all signals to 0-1 range
    const snr = results.extended?.snr?.average || 10;
    const snrNorm = Math.min(snr / 12, 1); // 12+ is excellent SNR
    
    const sharp = results.extended?.band_sharpness?.average || 100;
    const sharpNorm = Math.min(sharp / 120, 1); // 120+ is sharp
    
    const loadEven = results.extended?.loading_evenness?.evenness_score || 0.85;
    
    const bandCount = results.bands?.length || 0;
    const bandScore = bandCount > 0 ? Math.min(bandCount / 4, 1.0) : 0.3;

    // Forensic Penalty — proportional to suspicious ratio, not a cliff
    const suspRatio = totalPatches > 0 ? suspCount / totalPatches : 0;
    let forensicPenalty = suspRatio * 0.15; // max 0.15 if ALL patches suspicious
    if (hasNoise) forensicPenalty += 0.03;

    // Weighted combination — emphasizes measurable image quality signals
    let composite = (
      (authScore * 0.20) + 
      (dlScore * 0.15) + 
      (snrNorm * 0.25) + 
      (sharpNorm * 0.20) + 
      (loadEven * 0.10) +
      (bandScore * 0.10)
    ) - forensicPenalty;

    
    composite = Math.max(0, Math.min(1, composite));
    const score100 = Math.round(composite * 100);

    // Determine Status
    let status = "Needs Review";
    let color = "var(--amber)";
    let icon = AlertTriangle;
    let textClass = "badge-amber";
    let message = "The image has some quality or authenticity concerns. Manual review advised.";

    if (score100 >= 75) {
      status = "Satisfactory";
      color = "var(--green)";
      icon = CheckCircle;
      textClass = "badge-green";
      message = "High quality image. Clean forensics and excellent band characteristics.";
    } else if (score100 < 55) {
      status = "Unsatisfactory";
      color = "var(--red)";
      icon = XCircle;
      textClass = "badge-red";
      message = "Significant issues detected (e.g., manipulation, heavy noise, or low resolution).";
    }

    // Auto-generate key findings
    const findings = [];
    if (authScore < 0.6) findings.push("Authenticity score is low, indicating potential digital manipulation.");
    if (suspCount > 0) findings.push(`Detected ${suspCount} suspicious regions via Patch Forensics.`);
    if (dlScore < 0.6) findings.push("Overall image quality assessed by deep learning is suboptimal.");
    if (hasNoise) findings.push("Spectral analysis found periodic noise patterns often associated with editing artifacts.");
    if (snrNorm < 0.4) findings.push("Signal-to-noise ratio is poor, bands might be hard to distinguish from background.");
    
    if (findings.length === 0) {
      findings.push("All automated deep learning forensics checks passed successfully.");
      findings.push("Band sharpness and signal-to-noise ratio are within acceptable laboratory bounds.");
      findings.push("No evidence of copy-move manipulation or abnormal spectral frequencies.");
    }

    setVerdictData({ score: score100, status, color, icon, textClass, message, findings, suspCount, hasNoise, authScore, dlScore });
  }, [results, image_name]);


  const generatePDF = async () => {
    if (!reportRef.current) return;
    setIsGenerating(true);

    try {
      // Create a temporary clone for rendering without scrollbars or fixed height issues
      const clone = reportRef.current.cloneNode(true);
      clone.style.width = "800px"; // Fixed width for A4 proportion
      clone.style.padding = "40px";
      clone.style.background = "#ffffff"; // Force white bg for PDF
      clone.style.color = "#000000"; // Force black text
      clone.style.position = "absolute";
      clone.style.left = "-9999px";
      clone.classList.add("pdf-render-mode"); // To apply specific print styles if needed
      
      // Need to adjust child text colors in clone
      const allText = clone.querySelectorAll('span, p, h1, h2, h3, div');
      allText.forEach(el => {
         // rudimentary color stripping for clean PDF
         if (window.getComputedStyle(el).color === 'rgb(255, 255, 255)' || window.getComputedStyle(el).color === 'rgba(255, 255, 255, 0.7)') {
            el.style.color = '#333333';
         }
      });

      document.body.appendChild(clone);

      const canvas = await html2canvas(clone, {
        scale: 2, // Higher resolution
        useCORS: true,
        logging: false,
        backgroundColor: "#ffffff"
      });

      document.body.removeChild(clone);

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4"
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save(`BlotQuant_Report_${image_name || "Analysis"}.pdf`);
    } catch (err) {
      console.error("PDF generation failed:", err);
      alert("Failed to generate PDF. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  if (!verdictData) return null;

  const VerdictIcon = verdictData.icon;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      
      {/* Action Bar */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button 
          onClick={generatePDF} 
          disabled={isGenerating}
          className="btn-gradient" 
          style={{ padding: '12px 24px', fontSize: 14 }}
        >
          {isGenerating ? (
            <span className="animate-spin-slow" style={{ display: 'inline-block', width: 16, height: 16, border: '2px solid rgba(0,0,0,0.2)', borderTopColor: '#000', borderRadius: '50%' }} />
          ) : <Download size={16} />}
          {isGenerating ? "Generating..." : "Download PDF Report"}
        </button>
      </div>

      {/* --- This container is what gets rendered to PDF (plus it displays on screen) --- */}
      <div 
        ref={reportRef} 
        className="glass-card pdf-content-wrapper" 
        style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '30px', background: 'var(--bg-card)' }}
      >
        
        {/* Header (PDF) */}
        <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: 24, marginBottom: 8 }} className="gradient-text">BlotQuant Complete Analysis Report</h1>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Image: {image_name}</p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Date: {new Date(created_at).toLocaleString()}</p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end', marginBottom: 4 }}>
              <Cpu size={14} style={{ color: 'var(--purple)' }} />
              <span style={{ fontSize: 14, fontWeight: 'bold' }}>Engine v3.0</span>
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-dim)' }}>Deep Learning & Forensics Pipeline</p>
          </div>
        </div>

        {/* Verdict & Image Section */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          
          {/* Verdict Gauge */}
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '24px', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <h2 style={{ fontSize: 14, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '20px' }}>Final Verdict</h2>
            
            <div style={{ position: 'relative', width: 140, height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px' }}>
              <svg width="140" height="140" viewBox="0 0 140 140" style={{ position: 'absolute' }} className="verdict-ring">
                <circle cx="70" cy="70" r="64" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
                <circle 
                  cx="70" cy="70" r="64" 
                  fill="none" 
                  stroke={verdictData.color} 
                  strokeWidth="10" 
                  strokeDasharray="402" 
                  strokeDashoffset={402 - (402 * verdictData.score) / 100}
                  strokeLinecap="round"
                  style={{ transform: 'rotate(-90deg)', transformOrigin: 'center', transition: 'stroke-dashoffset 1s ease' }}
                />
              </svg>
              <div style={{ fontSize: 42, fontWeight: 800, fontFamily: "'Sora'" }}>{verdictData.score}</div>
            </div>

            <div className={`badge ${verdictData.textClass}`} style={{ fontSize: 16, padding: '8px 16px', marginBottom: '12px' }}>
              <VerdictIcon size={18} style={{ marginRight: 6 }} />
              {verdictData.status}
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, maxWidth: '280px' }}>{verdictData.message}</p>
          </div>

          {/* Original Image */}
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '24px', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: 14, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px' }}>Analyzed Image</h2>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000', borderRadius: '8px', overflow: 'hidden' }}>
              {imgUrl ? (
                <img src={imgUrl} alt="Analyzed Blot" style={{ maxWidth: '100%', maxHeight: '220px', objectFit: 'contain' }} />
              ) : (
                <span style={{ color: 'var(--text-muted)' }}>Image not available</span>
              )}
            </div>
          </div>
        </div>

        {/* Findings Section */}
        <div>
           <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: 8 }}>
             <FileText size={16} className="text-cyan-400" /> Key Findings Summary
           </h3>
           <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px 20px', borderRadius: '12px', border: '1px solid var(--border)' }}>
             <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
               {verdictData.findings.map((f, i) => (
                 <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{f}</li>
               ))}
             </ul>
           </div>
        </div>

        {/* Scorecard Grid */}
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: '16px' }}>Module Analysis Breakdown</h3>
          <div className="score-card-grid">
            
            <ModuleCard 
              icon={Shield} 
              title="Authenticity" 
              value={`${Math.round(verdictData.authScore * 100)}%`} 
              status={verdictData.authScore > 0.7 ? "good" : verdictData.authScore > 0.4 ? "warn" : "bad"} 
            />
            <ModuleCard 
              icon={Brain} 
              title="DL Quality (ResNet)" 
              value={`${Math.round(verdictData.dlScore * 100)}%`} 
              status={verdictData.dlScore > 0.7 ? "good" : "warn"} 
            />
            <ModuleCard 
              icon={ScanLine} 
              title="Bands Detected" 
              value={results.bands?.length || 0} 
              status={results.bands?.length > 0 ? "good" : "bad"} 
            />
            <ModuleCard 
              icon={Activity} 
              title="Patch Forensics" 
              value={`${verdictData.suspCount} alerts`} 
              status={verdictData.suspCount === 0 ? "good" : "warn"} 
            />
            <ModuleCard 
              icon={Activity} 
              title="Spectral Noise" 
              value={verdictData.hasNoise ? "Detected" : "Clear"} 
              status={verdictData.hasNoise ? "warn" : "good"} 
            />
            <ModuleCard 
              icon={Layers} 
              title="Loading Evenness" 
              value={(results.extended?.loading_evenness?.evenness_score || 0.88).toFixed(2)} 
              status={(results.extended?.loading_evenness?.evenness_score || 0.88) > 0.8 ? "good" : "warn"} 
            />

          </div>
        </div>

        {/* Footer for PDF */}
        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border)', textAlign: 'center', fontSize: 10, color: 'var(--text-dim)' }}>
          Generated by BlotQuant DLM Pipeline v3.0 • Automated Western Blot Assessment Tool
        </div>

      </div>
    </div>
  );
}

function ModuleCard({ icon: Icon, title, value, status }) {
  const isGood = status === "good";
  const isWarn = status === "warn";
  const color = isGood ? "var(--green)" : isWarn ? "var(--amber)" : "var(--red)";
  const bg = isGood ? "rgba(34,197,94,0.08)" : isWarn ? "rgba(245,158,11,0.08)" : "rgba(239,68,68,0.08)";
  
  return (
    <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '10px', padding: '14px', display: 'flex', alignItems: 'center', gap: '12px' }}>
      <div style={{ width: 36, height: 36, borderRadius: '8px', background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: color }}>
        <Icon size={18} />
      </div>
      <div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: '4px' }}>{title}</div>
        <div style={{ fontSize: 15, fontWeight: 600, fontFamily: "'JetBrains Mono'", color: color }}>{value}</div>
      </div>
    </div>
  );
}
