"use client";

import { createContext, useContext, useState, ReactNode, createElement } from "react";
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

  function setRole(newRole: string) {
    setRoleState(newRole);
    setApiRole(newRole);
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
