import { useState } from "react";

// Client-side pagination: slices `items` into pages of `itemsPerPage` and
// tracks the current page.
export function usePagination(items, itemsPerPage) {
  const [page, setPage] = useState(1);
  const totalPages = Math.max(1, Math.ceil(items.length / itemsPerPage));
  const paginated = items.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  return { page, setPage, totalPages, paginated };
}
