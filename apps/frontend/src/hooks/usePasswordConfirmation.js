import { useEffect, useState } from "react";

// Manages a password + confirm-password pair: clears both whenever `resetKey`
// changes (e.g. a new token read from the URL), and exposes whether they
// currently match plus the "requirements hint" modal toggle used alongside them.
export function usePasswordConfirmation(resetKey) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showHint, setShowHint] = useState(false);

  useEffect(() => {
    setPassword("");
    setConfirmPassword("");
  }, [resetKey]);

  const reset = () => {
    setPassword("");
    setConfirmPassword("");
  };

  return {
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    mismatch: password !== confirmPassword,
    reset,
    showHint,
    openHint: () => setShowHint(true),
    closeHint: () => setShowHint(false),
  };
}
