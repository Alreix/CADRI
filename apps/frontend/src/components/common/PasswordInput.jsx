import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function PasswordInput(props) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="password-field">
      <input
        {...props}
        type={visible ? "text" : "password"}
      />

      <button
        type="button"
        className="password-toggle"
        onClick={() => setVisible((isVisible) => !isVisible)}
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
}