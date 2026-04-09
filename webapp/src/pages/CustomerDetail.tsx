import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import CustomerCard, { type CustomerInfo } from "../components/CustomerCard";
import MachineList, { type Machine } from "../components/MachineList";
import OrderList, { type Order } from "../components/OrderList";
import CustomerSummary from "../components/CustomerSummary";
import {
  fetchCustomer,
  fetchCustomerByOrgNr,
  fetchCustomersByName,
  fetchMachines,
  fetchOrders,
} from "../api/dabClient";

export default function CustomerDetail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get("q") || "";
  const queryType =
    (searchParams.get("type") as "kundenummer" | "navn" | "org_nummer") ||
    "kundenummer";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [customer, setCustomer] = useState<CustomerInfo | null>(null);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);

  useEffect(() => {
    if (!query) return;
    loadData();
  }, [query, queryType]);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      let cust: CustomerInfo | null = null;

      if (queryType === "kundenummer") {
        cust = await fetchCustomer(Number(query));
      } else if (queryType === "org_nummer") {
        cust = await fetchCustomerByOrgNr(query);
      } else if (queryType === "navn") {
        const results = await fetchCustomersByName(query);
        cust = results.length > 0 ? results[0] : null;
      }

      if (!cust) {
        setError("Ingen kunde funnet.");
        setLoading(false);
        return;
      }

      setCustomer(cust);

      const [machineData, orderData] = await Promise.all([
        fetchMachines(cust.kundenummer),
        fetchOrders(cust.kundenummer),
      ]);

      setMachines(machineData);
      setOrders(orderData);
    } catch {
      setError("Kunne ikke hente data. Sjekk at backend kjorer.");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="detail-page">
        <div className="loading">Henter kundeinformasjon...</div>
      </div>
    );
  }

  return (
    <div className="detail-page">
      <button onClick={() => navigate("/")} className="btn btn-back">
        Tilbake til soek
      </button>

      {error && <div className="error-banner">{error}</div>}

      {customer && (
        <>
          <CustomerSummary kundenummer={customer.kundenummer} />
          <CustomerCard
            customer={customer}
            onLookupProff={() =>
              window.open(
                `https://www.proff.no/bransjes%C3%B8k?q=${customer.org_nummer}`,
                "_blank"
              )
            }
            onLookupAt={() =>
              window.open(
                `https://www.arbeidstilsynet.no/opendata/virksomheter/?orgNr=${customer.org_nummer}`,
                "_blank"
              )
            }
          />
          <MachineList
            machines={machines}
            selectedDeviceId={selectedDeviceId}
            onSelectMachine={(deviceId) =>
              setSelectedDeviceId((prev) =>
                prev === deviceId ? null : deviceId
              )
            }
          />
          <OrderList
            orders={
              selectedDeviceId
                ? orders.filter((o) => o.device_id === selectedDeviceId)
                : orders
            }
            filterLabel={
              selectedDeviceId
                ? machines.find((m) => m.device_id === selectedDeviceId)
                    ?.maskin_navn || selectedDeviceId
                : undefined
            }
          />
        </>
      )}
    </div>
  );
}
