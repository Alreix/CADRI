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