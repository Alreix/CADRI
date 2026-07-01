// Small pill/tag displaying a mission's priority and/or status, with color
// variants applied conditionally based on the value.
function StatusBadge({ priority, status }) {
  return (
    <>
      {priority === "Urgente" && (
        <span className="tag tag--urgent">Urgente</span>
      )}
      {status && (
        <span className={`tag${
          status === "En cours" ? " tag--in-progress" : ""
        }${
          status === "En attente de validation" ? " tag--validation" : ""
        }`}>
          {status}
        </span>
      )}
    </>
  );
}

export default StatusBadge;