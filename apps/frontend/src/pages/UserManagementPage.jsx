import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";
import UserFilters from "../components/user/UserFilters";
import UserTable from "../components/user/UserTable";
import { getUsers } from "../api/usersApi";
import { Search, SlidersHorizontal, ChevronLeft, ChevronRight } from "lucide-react";
import '../styles/UserManagementPage.css';


const items_per_page = 10;

const defaul_filters = {
  role: "",
  service: "",
};

function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState(defaul_filters);
  const [page, setPage] = useState(1);

  useEffect(() => {
    getUsers().then(setUsers);
  }, []);

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const services = [...new Set(users.map((user) => user.service))].filter(Boolean).sort();

  const filtered = users.filter((user) => {
    const term = search.toLowerCase();
    if (term && !user.firstName.toLowerCase().includes(term) && !user.lastName.toLowerCase().includes(term)) return false;
    if (filters.role && user.role !== filters.role) return false;
    if (filters.service && user.service !== filters.service) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / items_per_page));
  const paginated = filtered.slice((page - 1) * items_per_page, page * items_per_page);

  return (
    <Layout>
      <div className="page-header">
        <h1>Gestion des utilisateurs</h1>
        <Link to="/users/new" className="btn-voir">
          Créer un nouvel utilisateur
        </Link>
      </div>

      <div className="search-bar">
        <div className="search-input-wrapper">
          <Search
            className="search-input-icon"
            size={18}
            aria-hidden="true"
          />
          <input
            type="search"
            className="search-input"
            placeholder="Rechercher des utilisateurs..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </div>
        <button
          className="filter-btn"
          onClick={() => setShowFilters((toggleFilters) => !toggleFilters)}
          aria-expanded={showFilters}
        >
          <SlidersHorizontal size={18} aria-hidden="true" />
          <span>Filtres</span>
        </button>
      </div>

      {showFilters && (
        <UserFilters
          filters={filters}
          services={services}
          onChange={handleFiltersChange}
        />
      )}

      <UserTable users={paginated} />

      <div className="pagination">
        <button
          className="pagination-btn"
          onClick={() => setPage((currentPage) => currentPage - 1)}
          disabled={page === 1}
        >
          <ChevronLeft size={16} aria-hidden="true" />
          <span>Précédent</span>
        </button>
        {Array.from({ length: totalPages }, (_, index) => index + 1).map((pageNumber) => (
          <button
            key={pageNumber}
            className={`pagination-page ${pageNumber === page ? "pagination-page--active" : ""}`}
            onClick={() => setPage(pageNumber)}
          >
            {pageNumber}
          </button>
        ))}
        <button
          className="pagination-btn"
          onClick={() => setPage((prevPage) => prevPage + 1)}
          disabled={page === totalPages}
        >
          <span>Suivant</span>
          <ChevronRight size={16} aria-hidden="true" />
        </button>
      </div>
    </Layout>
  );
}

export default UserManagementPage;