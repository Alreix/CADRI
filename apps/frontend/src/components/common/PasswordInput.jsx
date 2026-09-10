// Password <input> with a show/hide toggle button. Wraps a native input and
// forwards any extra props (value, onChange, name, etc.) directly to it.
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function PasswordInput({ rightIcon, ...props }) {
  // Local-only UI state: whether the password is currently shown in plain text.
  const [visible, setVisible] = useState(false);

  return (
    <div className="password-field">
      <input
        {...props}
        type={visible ? "text" : "password"}
      />

      <button
        type="button"
        className={`password-toggle ${rightIcon ? "password-toggle-with-info" : ""}`}
        onClick={() => setVisible((isVisible) => !isVisible)}
        aria-label={
          visible
            ? "Masquer le mot de passe"
            : "Afficher le mot de passe"
        }
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>

      {/* Optional extra icon/button slot, e.g. a "password requirements" info button. */}
      {rightIcon}
    </div>
  );
}
