interface CustomerInfo {
  kundenummer: number;
  navn: string;
  adresse: string;
  epost: string;
  telefonnummer: string;
  org_nummer: string;
}

interface Props {
  customer: CustomerInfo;
  onLookupProff: () => void;
  onLookupAt: () => void;
}

export default function CustomerCard({
  customer,
  onLookupProff,
  onLookupAt,
}: Props) {
  return (
    <div className="card customer-card">
      <h2>{customer.navn}</h2>
      <table>
        <tbody>
          <tr>
            <td className="label">Kundenummer</td>
            <td>{customer.kundenummer}</td>
          </tr>
          <tr>
            <td className="label">Org.nummer</td>
            <td>{customer.org_nummer}</td>
          </tr>
          <tr>
            <td className="label">Adresse</td>
            <td>{customer.adresse}</td>
          </tr>
          <tr>
            <td className="label">E-post</td>
            <td>
              <a href={`mailto:${customer.epost}`}>{customer.epost}</a>
            </td>
          </tr>
          <tr>
            <td className="label">Telefon</td>
            <td>{customer.telefonnummer}</td>
          </tr>
        </tbody>
      </table>
      <div className="lookup-buttons">
        <button onClick={onLookupProff} className="btn btn-secondary">
          Slå opp på Proff.no
        </button>
        <button onClick={onLookupAt} className="btn btn-secondary">
          Slå opp på At.no
        </button>
      </div>
    </div>
  );
}

export type { CustomerInfo };
