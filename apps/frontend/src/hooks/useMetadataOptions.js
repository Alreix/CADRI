import { useEffect, useState } from "react";

// Loads a reference/lookup list (services, roles, statuses, ...) once on
// mount, keeping `initialValue` as a fallback if the request fails or comes
// back empty (avoids blank dropdowns/filters while it's in flight).
export function useMetadataOptions(fetchFn, initialValue = []) {
  const [options, setOptions] = useState(initialValue);

  useEffect(() => {
    fetchFn()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) setOptions(data);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return [options, setOptions];
}
