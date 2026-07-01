// Renders a list of mission cards (already filtered/paginated by the parent page).
// Purely presentational: receives a finished `missions` array as a prop and owns no state.
import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge";
import { formatDateFR } from "../../api/missionsApi";


function MissionList({ missions }) {
  if (missions.length === 0) {
    return (
      <p className="mission-empty">
        Aucune mission ne correspond à votre recherche.
      </p>
    );
  }

  return (
    <div className="mission-list">
      {missions.map((mission) => (
        <div key={mission.id} className="mission-card">
          <div className="mission-card-body">
            <p className="mission-card-title">{mission.title}</p>
            <div className="mission-card-tags">
              <StatusBadge priority={mission.priorityLabel} status={mission.statusLabel} />
              {mission.interventionType && (
                <span className="tag">{mission.interventionType}</span>
              )}
              {mission.service && (
                <span className="tag">{mission.service}</span>
              )}
            </div>
            <p className="mission-card-dates">
              {formatDateFR(mission.startDate)} - {formatDateFR(mission.endDate)}
            </p>
          </div>
          <Link to={`/missions/${mission.id}`} className="btn-view">
            Voir la mission
          </Link>
        </div>
      ))}
    </div>
  );
}

export default MissionList;