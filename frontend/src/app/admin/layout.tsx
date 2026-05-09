"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/shell/Sidebar";
import { useDevContext } from "@/lib/context";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { role } = useDevContext();
  const router = useRouter();

  useEffect(() => {
    if (role === "new_hire") {
      router.replace("/onboarding");
    }
  }, [role, router]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
