// Labeled password field for the auth pages (activation/reset), with the
// "requirements hint" info button wired into PasswordInput's rightIcon slot.
import { Info } from "lucide-react";
import PasswordInput from "./PasswordInput";

function PasswordFieldWithHint({ id, label, value, onChange, onShowHint }) {
  return (
    <div className="auth-field">
      <label className="auth-label" htmlFor={id}>
        {label}<span className="auth-label-required">*</span>
      </label>
      <PasswordInput
        id={id}
        name={id}
        className="auth-input"
        placeholder="••••••••"
        value={value}
        onChange={onChange}
        required
        autoComplete="new-password"
        rightIcon={
          <button
            type="button"
            className="auth-password-info-btn"
            onClick={onShowHint}
            aria-label="Voir les exigences du mot de passe"
          >
            <Info size={16} />
          </button>
        }
      />
    </div>
  );
}

export default PasswordFieldWithHint;
