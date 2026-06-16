const PASSWORD_REQUIREMENTS = [
  "Au moins 8 caractères",
  "Au moins une lettre majuscule",
  "Au moins une lettre minuscule",
  "Au moins un chiffre",
  "Au moins un caractère spécial",
];

function PasswordRequirementsModal({ onClose }) {
  return (
    <div className="confirm-modal-overlay" role="dialog" aria-modal="true">
      <div className="confirm-modal">
        <div className="confirm-modal-header">
          <span className="confirm-modal-title">Exigences du mot de passe</span>
          <button className="confirm-modal-close" onClick={onClose} aria-label="Fermer">✕</button>
        </div>
        <div className="confirm-modal-body">
          <p>Votre mot de passe doit respecter les exigences suivantes :</p>
          <ul className="pwd-req-list">
            {PASSWORD_REQUIREMENTS.map((req) => (
              <li key={req} className="pwd-req-item">
                <span className="pwd-req-check">✓</span>
                {req}
              </li>
            ))}
          </ul>
        </div>
        <div className="confirm-modal-footer">
          <button className="profile-btn-primary" onClick={onClose}>Compris</button>
        </div>
      </div>
    </div>
  );
}

export default PasswordRequirementsModal;