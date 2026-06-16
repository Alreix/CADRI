

function StatusBadge({ priority, status, type }) {
  if (type === "validation") {
    return <span className="tag tag--validation">Nécessite validation</span>;
  }

  if (priority === "Urgente") {
    return <span className="tag tag--urgent">Urgente</span>;
  }

  if (status) {
    return <span className="tag">{status}</span>;
  }

  return null;
}

export default StatusBadge;