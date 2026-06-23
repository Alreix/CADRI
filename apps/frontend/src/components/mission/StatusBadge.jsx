function StatusBadge({ priority, status, type }) {
  if (type === "validation") {
    return <span className="tag tag--validation">Nécessite validation</span>;
  }

  return (
    <>
      {priority === "Urgente" && (
        <span className="tag tag--urgent">Urgente</span>
      )}
      {status && (
        <span className={`tag${status === "En cours" ? " tag--in-progress" : ""}`}>
          {status}
        </span>
      )}
    </>
  );
}

export default StatusBadge;