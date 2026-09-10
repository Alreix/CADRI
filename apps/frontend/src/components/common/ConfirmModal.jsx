// Generic yes/no confirmation dialog (delete a record, log out, etc.).
// `danger` switches the confirm button to the red/destructive style.
import { X } from "lucide-react";

function ConfirmModal({
  title,
  message,
  onConfirm,
  onCancel,
  cancelLabel = "Annuler",
  confirmLabel = "Confirmer",
  danger = false,
}) {
  return (
    <div className="confirm-modal-overlay" role="dialog" aria-modal="true">
      <div className="confirm-modal">
        <div className="confirm-modal-header">
          <span className="confirm-modal-title">{title}</span>
          <button className="confirm-modal-close" onClick={onCancel} aria-label="Fermer">
            <X size={18} />
          </button>
        </div>
        <div className="confirm-modal-body">{message}</div>
        <div className="confirm-modal-footer">
          <button className="confirm-modal-cancel" onClick={onCancel}>{cancelLabel}</button>
          <button
            className={danger ? "confirm-modal-confirm-danger" : "confirm-modal-confirm-primary"}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
