interface Machine {
  device_id: string;
  maskin_navn: string;
  aarsmodell: number;
  chassisnummer: string;
}

interface Props {
  machines: Machine[];
  selectedDeviceId?: string | null;
  onSelectMachine?: (deviceId: string) => void;
}

export default function MachineList({
  machines,
  selectedDeviceId,
  onSelectMachine,
}: Props) {
  if (machines.length === 0) {
    return (
      <div className="card">
        <h3>Maskiner</h3>
        <p className="empty-state">Ingen maskiner registrert</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>
        Maskiner ({machines.length} stk)
        {selectedDeviceId && (
          <span className="filter-hint"> — klikk maskinen igjen for aa vise alle ordrer</span>
        )}
      </h3>
      <div className="table-container">
        <table className="data-table machine-table">
          <thead>
            <tr>
              <th>Device ID</th>
              <th>Maskin</th>
              <th>Aarsmodell</th>
              <th>Chassisnummer</th>
            </tr>
          </thead>
          <tbody>
            {machines.map((m) => (
              <tr
                key={m.device_id}
                className={`machine-row ${selectedDeviceId === m.device_id ? "machine-selected" : ""}`}
                onClick={() => onSelectMachine?.(m.device_id)}
              >
                <td className="mono">{m.device_id}</td>
                <td>{m.maskin_navn}</td>
                <td>{m.aarsmodell}</td>
                <td className="mono">{m.chassisnummer}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export type { Machine };
