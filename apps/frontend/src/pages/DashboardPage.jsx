// Home page after login: shows mission stats, search/filter controls, and a
// paginated list. Filtering, sorting and pagination are all done client-side
// on the already-loaded missions (see comments below for why).
import { useContext, useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import MissionFilters from "../components/mission/MissionFilters";
import MissionList from "../components/mission/MissionList";
import { AuthContext } from "../contexts/AuthContext";
import { getMissions } from "../api/missionsApi";
import "../styles/DashboardPage.css";
import {
  Clock3,
  TriangleAlert,
  Search,
  SlidersHorizontal,
} from "lucide-react";

const items_per_page = 5;

// Initial/reset state for the filter panel.
const default_filters = {
  statuses: [],
  myMissions: false,
  priority: "",
  startDate: "",
  endDate: "",
};

function DashboardPage() {
  const { user } = useContext(AuthContext);
  const [missions, setMissions] = useState([]);
  const [stats, setStats] = useState({ inProgressCount: 0, urgentCount: 0 });
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState(default_filters);
  const [page, setPage] = useState(1);

  // Fetch missions from the API whenever the "my missions only" toggle changes.
  // Other filters (status, priority, search, dates) are applied client-side below,
  // since they only narrow down a dataset that's already small enough to keep in memory.
  useEffect(() => {
    getMissions({
      myMissions: filters.myMissions,
      perPage: 10,
    }).then((data) => {
      setMissions(data);
      const activeMissions = data.filter((mission) => mission.status !== "completed");
      setStats({
        inProgressCount: activeMissions.filter((mission) => mission.status === "in_progress").length,
        urgentCount: activeMissions.filter((mission) => mission.priority === "high").length,
      });
    });
  }, [filters.myMissions]);

  // Reset to page 1 whenever the filters change, so the user doesn't land
  // on an out-of-range page after narrowing the results.
  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  // Client-side filtering: applied on the dataset already loaded in `missions`.
  const filtered = missions.filter((mission) => {
    if (search && !mission.title.toLowerCase().includes(search.toLowerCase())) return false;
    if (filters.statuses.length && !filters.statuses.includes(mission.status)) return false;
    // By default (no status filter selected), hide completed missions to keep the list focused.
    if (!filters.statuses.length && mission.status === "completed") return false;
    if (
      filters.myMissions &&
      !mission.assignedUsers?.some((assignedUserId) => String(assignedUserId) === String(user?.id))
    ) return false;
    if (filters.priority && mission.priority !== filters.priority) return false;
    if (filters.startDate && mission.startDate < filters.startDate) return false;
    if (filters.endDate && mission.endDate > filters.endDate) return false;
    return true;
  }).sort((currentMission, nextMission) => {
    // Sort order: urgent missions first, then by date, then alphabetically by title.
    const currentPriorityOrder = currentMission.priority === "high" ? 0 : 1;
    const nextPriorityOrder = nextMission.priority === "high" ? 0 : 1;

    if (currentPriorityOrder !== nextPriorityOrder) {
      return currentPriorityOrder - nextPriorityOrder;
    }

    const currentDate = currentMission.startDate || currentMission.endDate || "";
    const nextDate = nextMission.startDate || nextMission.endDate || "";
    const dateOrder = currentDate.localeCompare(nextDate);

    if (dateOrder !== 0) return dateOrder;
    return currentMission.title.localeCompare(nextMission.title);
  });

  // Slice the filtered/sorted list into the current page.
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
          <div className="stat-card-icon stat-card-icon--blue" aria-hidden="true">
            <Clock3 size={24} />
          </div>
        </div>
        <div className="stat-card">
          <div>
            <p className="stat-card-label">Missions urgentes</p>
            <p className="stat-card-value stat-card-value--urgent">{stats.urgentCount}</p>
          </div>
          <div className="stat-card-icon stat-card-icon--red" aria-hidden="true">
            <TriangleAlert size={24} />
          </div>
        </div>
      </div>

      <div className="search-bar">
        <div className="search-input-wrapper">
          <Search
            size={18}
            className="search-input-icon"
            aria-hidden="true"
          />
          <input
            type="search"
            className="search-input"
            placeholder="Rechercher des missions..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </div>
        <button
          className="filter-btn"
          onClick={() => setShowFilters((isVisible) => !isVisible)}
          aria-expanded={showFilters}
        >
          <SlidersHorizontal size={18} aria-hidden="true" />
          <span>Filtres</span>
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
