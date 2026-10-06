import { useEffect, useRef } from "react";

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

// Standard dialog accessibility behavior: moves focus into the dialog when it
// opens, traps Tab navigation inside it, closes on Escape, and restores focus
// to whatever triggered it once it unmounts. Attach the returned ref to the
// dialog's outer element.
export function useModalAccessibility(onClose) {
  const containerRef = useRef(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement;
    const container = containerRef.current;
    const focusables = container ? container.querySelectorAll(FOCUSABLE_SELECTOR) : [];
    (focusables[0] || container)?.focus();

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
        return;
      }

      if (event.key !== "Tab" || !container) return;

      const items = container.querySelectorAll(FOCUSABLE_SELECTOR);
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus?.();
    };
  }, [onClose]);

  return containerRef;
}
