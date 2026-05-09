"use client";

import { createContext, useContext, useState, useEffect, ReactNode, createElement } from "react";
import { DEV_ORG_ID, DEV_USER_ID, DEV_USER_ROLE, setApiRole } from "./api";

interface DevContextValue {
  orgId: string;
  userId: string;
  role: string;
  setRole: (role: string) => void;
}

const DevContext = createContext<DevContextValue>({
  orgId: DEV_ORG_ID,
  userId: DEV_USER_ID,
  role: DEV_USER_ROLE,
  setRole: () => {},
});

export function DevContextProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState(DEV_USER_ROLE);

  useEffect(() => {
    const stored = localStorage.getItem("lex-role");
    if (stored && stored !== DEV_USER_ROLE) {
      setRoleState(stored);
      setApiRole(stored);
    }
  }, []);

  function setRole(newRole: string) {
    setRoleState(newRole);
    setApiRole(newRole);
    localStorage.setItem("lex-role", newRole);
  }

  return createElement(
    DevContext.Provider,
    { value: { orgId: DEV_ORG_ID, userId: DEV_USER_ID, role, setRole } },
    children,
  );
}

export function useDevContext(): DevContextValue {
  return useContext(DevContext);
}
