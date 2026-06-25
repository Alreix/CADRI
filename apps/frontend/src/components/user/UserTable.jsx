import { useNavigate } from "react-router-dom";


function UserTable({ users }) {
  const navigate = useNavigate();

  return (
    <div className="users-table-wrapper">
      <table className="users-table">
        <thead>
          <tr>
            <th>Prénom</th>
            <th>Nom</th>
            <th>Service</th>
            <th>Rôle</th>
            <th>Action</th>
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