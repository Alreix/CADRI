import { useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import MissionFilters from "../components/mission/MissionFilters";
import MissionList from "../components/mission/MissionList";
import { getMissions } from "../api/missionsApi";
import "../styles/DashboardPage.css";

const items_per_page = 5;

const default_filters = {
  statuses: [],
  myMissions: false,
  priority: "",
  startDate: "",
  endDate: "",
};

function DashboardPage({ user }) {
  const [missions, setMissions] = useState([]);
  const [stats, setStats] = useState({ inProgressCount: 0, urgentCount: 0 });
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState(default_filters);
  const [page, setPage] = useState(1);

  useEffect(() => {
    getMissions().then((data) => {
      setMissions(data);
      setStats({
        inProgressCount: data.filter((mission) => mission.status === "En cours").length,
        urgentCount: data.filter((mission) => mission.priority === "Urgente").length,
      });
    });
  }, []);

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const filtered = missions.filter((mission) => {
    if (search && !mission.title.toLowerCase().includes(search.toLowerCase())) return false;
    if (filters.statuses.length && !filters.statuses.includes(mission.status)) return false;
    if (filters.myMissions && mission.agentId !== user?.id) return false;
    if (filters.priority && mission.priority !== filters.priority) return false;
    if (filters.startDate && mission.startDate < filters.startDate) return false;
    if (filters.endDate && mission.endDate > filters.endDate) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / items_per_page));
  const paginated = filtered.slice((page - 1) * items_per_page, page * items_per_page);

  return (
    <Layout user={user}>
      <div className="page-header">
        <h1>Tableau de bord</h1>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div>
            <p className="stat-card-label">Missions en cours</p>
            <p className="stat-card-value">{stats.inProgressCount}</p>
          </div>
          <div className="stat-card-icon stat-card-icon--blue" aria-hidden="true">🕐</div>
        </div>
        <div className="stat-card">
          <div>
            <p className="stat-card-label">Missions urgentes</p>
            <p className="stat-card-value stat-card-value--urgent">{stats.urgentCount}</p>
          </div>
          <div className="stat-card-icon stat-card-icon--red" aria-hidden="true">⚠</div>
        </div>
      </div>

      <div className="search-bar">
        <div className="search-input-wrapper">
          <span className="search-input-icon" aria-hidden="true">🔍</span>
          <input
            type="search"
            className="search-input"
            placeholder="Rechercher des missions..."
            value={search}
            onChange={(event) => { setSearch(event.target.value); setPage(1); }}
          />
        </div>
        <button
          className="filter-btn"
          onClick={() => setShowFilters((isVisible) => !isVisible)}
          aria-expanded={showFilters}
        >
          ⧉ Filtres
        </button>
      </div>

      {showFilters && (
        <MissionFilters filters={filters} onChange={handleFiltersChange} />
      )}

      <MissionList missions={paginated} />

      <div className="pagination">
        <button
          className="pagination-btn"
          onClick={() => setPage((currentPage) => currentPage - 1)}
          disabled={page === 1}
        >
          &lt; Précédent
        </button>
        {Array.from({ length: totalPages }, (_, idx) => idx + 1).map((currentPage) => (
          <button
            key={currentPage}
            className={`pagination-page ${currentPage === page ? "pagination-page--active" : ""}`}
            onClick={() => setPage(currentPage)}
          >
            {currentPage}
          </button>
        ))}
        <button
          className="pagination-btn"
          onClick={() => setPage((currentPage) => currentPage + 1)}
          disabled={page === totalPages}
        >
          Suivant &gt;
        </button>
      </div>
    </Layout>
  );
}

export default DashboardPage;