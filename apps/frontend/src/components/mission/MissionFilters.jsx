// Filter panel for the mission list (DashboardPage). Purely "controlled":
// it doesn't own the filter state itself, it receives `filters` and reports
// any change to the parent via `onChange`.
import { useEffect, useState } from "react";
import { getPriorities, getStatuses } from "../../api/metadataApi";
import "../../styles/MissionFilters.css";


function MissionFilters({ filters, onChange }) {
  // Hardcoded fallback options, replaced by the real backend list once it loads
  // (avoids an empty filter panel while the metadata request is in flight).
  const [statuses, setStatuses] = useState([
    { value: "to_do", label: "À faire" },
    { value: "in_progress", label: "En cours" },
    { value: "completed", label: "Terminée" },
  ]);
  const [priorities, setPriorities] = useState([
    { value: "high", label: "Urgente" },
    { value: "medium", label: "Moyenne" },
    { value: "low", label: "Basse" },
  ]);

  // Load the real reference data once when the component mounts.
  useEffect(() => {
    getStatuses()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          // "remark_pending_validation" is an internal workflow status, not meant
          // to be used as a manual filter option.
          setStatuses(data.filter((status) => status.value !== "remark_pending_validation"));
        }
      })
      .catch(() => { });

    getPriorities()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) setPriorities(data);
      })
      .catch(() => { });
  }, []);

  // Status filter is multi-select: toggles a single status in/out of the active list.
  const handleStatus = (statusToToggle) => {
    const statuses = filters.statuses.includes(statusToToggle)
      ? filters.statuses.filter((status) => status !== statusToToggle)
      : [...filters.statuses, statusToToggle];
    onChange({ ...filters, statuses });
  };

  return (
    <div className="mission-filters-panel">
      <p className="mission-filters-title">Filtrer les missions</p>
      <div className="mission-filters-grid">

        <div className="filter-group">
          <span className="filter-label">Statut</span>
          <div className="filter-checkboxes">
            {statuses.map((status) => (
              <label key={status.value} className="filter-checkbox-item">
                <input
                  type="checkbox"
                  checked={filters.statuses.includes(status.value)}
                  onChange={() => handleStatus(status.value)}
                />
                {status.label}
              </label>
            ))}
          </div>
        </div>

        <div className="filter-group" style={{ paddingTop: "24px" }}>
          <label className="filter-checkbox-item">
            <input
              type="checkbox"
              checked={filters.myMissions}
              onChange={(event) => onChange({ ...filters, myMissions: event.target.checked })}
            />
            Mes missions uniquement
          </label>
        </div>

        <div className="filter-group">
          <span className="filter-label">Priorité</span>
          <select
            className="filter-select"
            value={filters.priority}
            onChange={(event) => onChange({ ...filters, priority: event.target.value })}
          >
            <option value="">Toutes</option>
            {priorities.map((priority) => (
              <option key={priority.value} value={priority.value}>{priority.label}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <span className="filter-label">Date de début à partir du</span>
          <input
            type="date"
            className="filter-date-input"
            value={filters.startDate}
            onChange={(event) => onChange({ ...filters, startDate: event.target.value })}
          />
        </div>

        <div className="filter-group">
          <span className="filter-label">Date de fin jusqu'au</span>
          <input
            type="date"
            className="filter-date-input"
            value={filters.endDate}
            onChange={(event) => onChange({ ...filters, endDate: event.target.value })}
          />
        </div>

      </div>
    </div>
  );
}

export default MissionFilters;
