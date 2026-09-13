// Renders the user list as a table (already filtered/paginated by UserManagementPage).
// Purely presentational, navigation to the detail page is the only side effect here.
import { useNavigate } from "react-router-dom";


function UserTable({ users }) {
  const navigate = useNavigate();

  return (
    <div className="users-table-wrapper">
      <table className="users-table">
        <thead>
          <tr>
            <th scope="col">Prénom</th>
            <th scope="col">Nom</th>
            <th scope="col">Service</th>
            <th scope="col">Rôle</th>
            <th scope="col">Action</th>
          </tr>
        </thead>
        <tbody>
          {users.length === 0 && (
            <tr>
              <td colSpan={5} className="users-table-empty">
                Aucun utilisateur ne correspond à votre recherche.
              </td>
            </tr>
          )}
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.firstName}</td>
              <td>{user.lastName}</td>
              <td>{user.service}</td>
              <td>
                {/* "responsable" maps to the "manager" CSS variant; other roles use their own name directly. */}
                <span className={`role-badge role-badge--${user.role === "responsable" ? "manager" : user.role}`}>
                  {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                </span>
              </td>
              <td>
                <button
                  className="table-action-link"
                  onClick={() => navigate(`/users/${user.id}`)}
                >
                  Voir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default UserTable;