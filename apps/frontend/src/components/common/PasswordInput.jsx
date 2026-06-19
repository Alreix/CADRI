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

            {rightIcon}
        </div>
    );
}