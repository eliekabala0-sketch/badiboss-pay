import { Navigate } from "react-router-dom";

import { getStoredToken } from "../auth";

type Props = {
  children: JSX.Element;
};

function ProtectedRoute({ children }: Props) {
  const token = getStoredToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default ProtectedRoute;
