// Explains the "*" convention used on required form fields (WCAG 3.3.2 /
// RGAA): placed at the top of every form that marks fields with an asterisk.
function RequiredFieldsNote() {
  return (
    <p className="required-fields-note">
      Les champs marqués d'un <span className="required-fields-note-star">*</span> sont obligatoires.
    </p>
  );
}

export default RequiredFieldsNote;
