import { useState, useRef, useCallback } from "react";
import { Upload, X, Image as ImageIcon, Zap } from "lucide-react";

export default function UploadZone({ onFileSelect, disabled }) {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const inputRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file) return;
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type) || file.size > 10 * 1024 * 1024) return;
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault(); setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const clearFile = () => { setSelectedFile(null); setPreview(null); if (inputRef.current) inputRef.current.value = ""; };

  return (
    <div>
      {!preview ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          className={`upload-zone ${dragActive ? 'active' : ''}`}
          style={{ opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
          data-testid="upload-dropzone"
        >
          <div style={{
            width: 56, height: 56, borderRadius: 16, marginBottom: 16,
            background: 'var(--gradient-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: '1px solid rgba(0,242,255,0.1)',
          }}>
            <Upload size={22} style={{ color: 'var(--cyan)', opacity: 0.7 }} />
          </div>
          <p style={{ fontSize: 16, fontWeight: 600, color: '#fff', marginBottom: 4, fontFamily: "'Sora'" }}>
            Drop your western blot image here
          </p>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>or click to browse</p>
          <div style={{ display: 'flex', gap: 6 }}>
            {["JPEG", "PNG", "WEBP"].map(f => (
              <span key={f} style={{
                padding: '2px 8px', borderRadius: 50, fontSize: 10, fontWeight: 500,
                background: 'rgba(255,255,255,0.04)', color: 'var(--text-muted)',
                border: '1px solid rgba(255,255,255,0.06)', fontFamily: "'JetBrains Mono'"
              }}>{f}</span>
            ))}
            <span style={{ padding: '2px 8px', borderRadius: 50, fontSize: 10, color: 'var(--text-dim)', fontFamily: "'JetBrains Mono'" }}>
              MAX 10 MB
            </span>
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: 16 }} data-testid="upload-preview">
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <div style={{ width: 100, height: 100, borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border)', flexShrink: 0 }}>
              <img src={preview} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                <ImageIcon size={13} style={{ color: 'var(--text-muted)' }} />
                <span style={{ fontSize: 13, fontWeight: 500, color: '#fff' }}>{selectedFile?.name}</span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono'", marginBottom: 14 }}>
                {(selectedFile?.size / 1024).toFixed(1)} KB
              </p>
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={() => onFileSelect(selectedFile)} disabled={disabled}
                  className="btn-gradient" data-testid="analyze-button"
                  style={{ opacity: disabled ? 0.5 : 1, padding: '8px 18px', fontSize: 12 }}>
                  <Zap size={13} /> {disabled ? "Analyzing..." : "Run Analysis"}
                </button>
                <button onClick={clearFile} disabled={disabled} className="btn-outline" style={{ padding: '8px 12px' }}>
                  <X size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" style={{ display: 'none' }}
        onChange={(e) => handleFile(e.target.files?.[0])} data-testid="upload-input" />
    </div>
  );
}
