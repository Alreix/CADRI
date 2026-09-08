import { useState } from "react";

// Single-object form state with a `setField(name, value)` helper, to avoid
// repeating `setForm(prev => ({ ...prev, [name]: value }))` for every field.
export function useFormState(initialValues) {
  const [form, setForm] = useState(initialValues);

  const setField = (name, value) => {
    setForm((prevForm) => ({ ...prevForm, [name]: value }));
  };

  return [form, setForm, setField];
}
