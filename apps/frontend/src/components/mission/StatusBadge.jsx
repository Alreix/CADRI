// Small pill/tag displaying a mission's priority and/or status, with color
// variants applied conditionally based on the value.
import "../../styles/StatusBadge.css";

const statusModifiers = {
  "À faire": " tag--to-do",
  "En cours": " tag--in-progress",
  "En attente de validation": " tag--validation",
  Terminée: " tag--completed",
};

function StatusBadge({ priority, status }) {
  return (
    <>
      {priority === "Urgente" && <span className="tag tag--urgent">Urgente</span>}
      {status && <span className={`tag${statusModifiers[status] ?? ""}`}>{status}</span>}
    </>
  );
}

export default StatusBadge;
