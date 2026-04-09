/**
 * REST client for Data API Builder (DAB).
 * Calls the DAB endpoint via the server.js /dab/* proxy.
 */

import type { CustomerInfo } from "../components/CustomerCard";
import type { Machine } from "../components/MachineList";
import type { Order } from "../components/OrderList";

const DAB_URL = "/dab";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function fetchAllPages(url: string): Promise<any[]> {
  const allItems: unknown[] = [];
  let nextUrl: string | null = url;

  while (nextUrl) {
    const res = await fetch(nextUrl);
    if (!res.ok) throw new Error(`DAB error: ${res.status}`);
    const data = await res.json();
    allItems.push(...(data.value || []));
    // DAB nextLink is absolute URL pointing to MCP server; rewrite to use our proxy
    if (data.nextLink) {
      const nl = new URL(data.nextLink);
      nextUrl = `${DAB_URL}${nl.pathname.replace(/^\/api/, "")}${nl.search}`;
    } else {
      nextUrl = null;
    }
  }
  return allItems;
}

export async function fetchCustomer(
  kundenummer: number
): Promise<CustomerInfo> {
  const res = await fetch(
    `${DAB_URL}/Customers/kundenummer/${kundenummer}`
  );
  if (!res.ok) throw new Error(`DAB error: ${res.status}`);
  const data = await res.json();
  return data.value?.[0] || data;
}

export async function fetchCustomerByOrgNr(
  orgNr: string
): Promise<CustomerInfo | null> {
  const items = await fetchAllPages(`${DAB_URL}/Customers`);
  return (
    (items as CustomerInfo[]).find(
      (c) => c.org_nummer === orgNr
    ) || null
  );
}

export async function fetchCustomersByName(
  name: string
): Promise<CustomerInfo[]> {
  const items = await fetchAllPages(`${DAB_URL}/Customers`);
  const lower = name.toLowerCase();
  return (items as CustomerInfo[]).filter((c) =>
    c.navn.toLowerCase().includes(lower)
  );
}

export async function fetchMachines(
  kundenummer: number
): Promise<Machine[]> {
  const items = await fetchAllPages(`${DAB_URL}/Machines`);
  return (items as (Machine & { kundenummer: number })[]).filter(
    (m) => m.kundenummer === kundenummer
  );
}

export async function fetchOrders(
  kundenummer: number
): Promise<Order[]> {
  const items = await fetchAllPages(`${DAB_URL}/Orders`);
  return (items as (Order & { kundenummer: number })[]).filter(
    (o) => o.kundenummer === kundenummer
  );
}
