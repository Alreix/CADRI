

function UserFilters({ filters, services, onChange }) {
  return (
    <div className="user-filters-panel">
      <p className="user-filters-title">Filtrer les utilisateurs</p>
      <div className="user-filters-grid">

        <div className="filter-group">
          <label className="filter-label" htmlFor="filter-role">Rôle</label>
          <select
            id="filter-role"
            className="filter-select"
            value={filters.role}
            onChange={(event) => onChange({ ...filters, role: event.target.value })}
          >
            <option value="">Tous</option>
            <option value="admin">Admin</option>
            <option value="manager">Responsable</option>
            <option value="agent">Agent</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="filter-service">Service</label>
          <select
            id="filter-service"
            className="filter-select"
            value={filters.service}
            onChange={(event) => onChange({ ...filters, service: event.target.value })}
          >
            <option value="">Tous</option>
            {services.map((service) => (
              <option key={service} value={service}>{service}</option>
            ))}
          </select>
        </div>

      </div>
    </div>
  );
}

export default UserFilters;