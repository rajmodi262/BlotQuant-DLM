export default function UncertaintyTable({ bands, uncertainty }) {
  if (!bands?.length) return null;
  return (
    <div data-testid="uncertainty-table" style={{ overflowX: 'auto' }}>
      <table className="data-table">
        <thead><tr><th>Band</th><th>Lane</th><th>MW (kDa)</th><th>Intensity</th><th>Std Dev</th><th>CI Lower</th><th>CI Upper</th><th>Conf</th></tr></thead>
        <tbody>
          {bands.map((b) => {
            const u = uncertainty?.find((x) => x.band_id === b.id);
            return (
              <tr key={b.id}>
                <td style={{ color: '#fff', fontWeight: 500 }}>Band {b.id}</td>
                <td>L{b.lane}</td><td>{b.molecular_weight_kda}</td>
                <td style={{ color: b.intensity >= 0.9 ? 'var(--green)' : 'var(--cyan)', fontWeight: 600 }}>{b.intensity?.toFixed(3)}</td>
                <td>{u?.std_dev?.toFixed(4) || "—"}</td><td>{u?.ci_lower?.toFixed(3) || "—"}</td><td>{u?.ci_upper?.toFixed(3) || "—"}</td><td>{u?.confidence?.toFixed(2) || "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
