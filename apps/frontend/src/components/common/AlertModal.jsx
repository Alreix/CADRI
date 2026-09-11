// Simple blocking alert dialog used to surface API/validation errors to the user.
import { X } from "lucide-react";
import { useModalAccessibility } from "../../hooks/useModalAccessibility";

function AlertModal({ message, onClose }) {
  const containerRef = useModalAccessibility(onClose);

  return (
    <div className="confirm-modal-overlay" role="dialog" aria-modal="true">
      <div className="confirm-modal" ref={containerRef} tabIndex={-1}>
        <div className="confirm-modal-header">
          <span className="confirm-modal-title">Attention</span>
          <button className="confirm-modal-close" onClick={onClose} aria-label="Fermer">
            <X size={18} />
          </button>
        </div>
        <div className="confirm-modal-body">{message}</div>
        <div className="confirm-modal-footer">
          <button className="confirm-modal-confirm-primary" onClick={onClose}>OK</button>
        </div>
      </div>
    </div>
  );
}

export default AlertModal;
