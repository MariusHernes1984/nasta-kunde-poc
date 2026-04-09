import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function CustomerSearch() {
  const [query, setQuery] = useState("");
  const [queryType, setQueryType] = useState<
    "kundenummer" | "navn" | "org_nummer"
  >("kundenummer");
  const navigate = useNavigate();

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(
      `/kunde?type=${queryType}&q=${encodeURIComponent(query.trim())}`
    );
  }

  return (
    <div className="search-page">
      <div className="search-container">
        <h1>Nasta AS - Kundeoppslag</h1>
        <p className="subtitle">
          Soek etter kunder med kundenummer, navn eller organisasjonsnummer
        </p>
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-type-row">
            <label className={queryType === "kundenummer" ? "active" : ""}>
              <input
                type="radio"
                name="type"
                value="kundenummer"
                checked={queryType === "kundenummer"}
                onChange={() => setQueryType("kundenummer")}
              />
              Kundenummer
            </label>
            <label className={queryType === "navn" ? "active" : ""}>
              <input
                type="radio"
                name="type"
                value="navn"
                checked={queryType === "navn"}
                onChange={() => setQueryType("navn")}
              />
              Navn
            </label>
            <label className={queryType === "org_nummer" ? "active" : ""}>
              <input
                type="radio"
                name="type"
                value="org_nummer"
                checked={queryType === "org_nummer"}
                onChange={() => setQueryType("org_nummer")}
              />
              Org.nummer
            </label>
          </div>
          <div className="search-input-row">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                queryType === "kundenummer"
                  ? "F.eks. 1001"
                  : queryType === "navn"
                    ? "F.eks. Berge AS"
                    : "F.eks. 912345678"
              }
              className="search-input"
            />
            <button type="submit" className="btn btn-primary">
              Soek
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
