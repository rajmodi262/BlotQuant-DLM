import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Component Error Caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', margin: '20px auto', maxWidth: '600px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--red)', marginBottom: '12px' }}>
            Component Rendering Error
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '20px', fontSize: '14px' }}>
            A UI component crashed while trying to render the analysis results. The underlying data might be missing or malformed.
          </p>
          <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', textAlign: 'left', fontSize: '11px', color: 'var(--text-muted)', overflowX: 'auto', marginBottom: '20px' }}>
            {this.state.error?.toString()}
          </pre>
          <button 
            onClick={() => window.location.reload()} 
            className="btn-gradient"
            style={{ padding: '10px 20px', fontSize: '14px' }}
          >
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
