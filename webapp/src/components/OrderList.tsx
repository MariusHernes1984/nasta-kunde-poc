interface Order {
  ordrenummer: string;
  ordretype: string;
  beskrivelse: string;
  device_id: string;
  status: string;
  opprettet_dato: string;
  symptomer_feil: string;
}

interface Props {
  orders: Order[];
}

function statusBadgeClass(status: string): string {
  switch (status) {
    case "Mottatt":
      return "badge badge-mottatt";
    case "Under behandling":
      return "badge badge-behandling";
    case "Ferdig":
      return "badge badge-ferdig";
    case "Avsluttet":
      return "badge badge-avsluttet";
    default:
      return "badge";
  }
}

export default function OrderList({ orders }: Props) {
  if (orders.length === 0) {
    return (
      <div className="card">
        <h3>Ordrer</h3>
        <p className="empty-state">Ingen ordrer registrert</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>Ordrer ({orders.length} stk)</h3>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Ordrenr</th>
              <th>Type</th>
              <th>Beskrivelse</th>
              <th>Maskin</th>
              <th>Status</th>
              <th>Opprettet</th>
              <th>Symptomer/Feil</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.ordrenummer}>
                <td className="mono">{o.ordrenummer}</td>
                <td>{o.ordretype}</td>
                <td>{o.beskrivelse}</td>
                <td className="mono">{o.device_id}</td>
                <td>
                  <span className={statusBadgeClass(o.status)}>
                    {o.status}
                  </span>
                </td>
                <td>{o.opprettet_dato}</td>
                <td>{o.symptomer_feil}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export type { Order };
