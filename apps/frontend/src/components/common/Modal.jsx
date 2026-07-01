// Simple reusable error/info modal. Fully controlled by the parent: it has no
// internal open/close state, the parent shows/hides it by rendering it conditionally.
import { CircleX, X } from "lucide-react";

function Modal({ title, message, onClose }) {
  return (
    <div className="auth-modal-overlay" role="dialog" aria-modal="true">
      <div className="auth-modal">
        <div className="auth-modal-header">
          <span className="auth-modal-title">{title}</span>
          <button className="auth-modal-close" onClick={onClose} aria-label="Fermer">
            <X size={18} />
          </button>
        </div>
        <div className="auth-modal-body">
          <span className="auth-modal-icon-error" aria-hidden="true">
            <CircleX
              size={20}
              className="auth-modal-icon-error"
              aria-hidden="true"
            />
          </span>
          <span>{message}</span>
        </div>
        <div className="auth-modal-footer">
          <button className="auth-modal-btn-ok" onClick={onClose}>OK</button>
        </div>
      </div>
    </div>
  );
}

export default Modal;