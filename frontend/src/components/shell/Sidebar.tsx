"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid,
  Upload,
  BookOpen,
  Settings,
  Home,
  Book,
  CheckCircle,
  List,
  MessageSquare,
} from "lucide-react";
import { useDevContext } from "@/lib/context";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const ADMIN_NAV: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: <LayoutGrid size={18} /> },
  { label: "Documents", href: "/dashboard/upload", icon: <Upload size={18} /> },
  { label: "Playbook", href: "/dashboard/playbook", icon: <Book size={18} /> },
  { label: "Settings", href: "/dashboard/settings", icon: <Settings size={18} /> },
];

const NEW_HIRE_NAV: NavItem[] = [
  { label: "My Onboarding", href: "/onboarding", icon: <Home size={18} /> },
  { label: "Textbook", href: "/onboarding/textbook", icon: <BookOpen size={18} /> },
  { label: "Quizzes", href: "/onboarding/quiz", icon: <CheckCircle size={18} /> },
  { label: "Contract Checklist", href: "/onboarding/checklist", icon: <List size={18} /> },
  { label: "Ask the Playbook", href: "/onboarding/chat", icon: <MessageSquare size={18} /> },
];

export function Sidebar() {
  const pathname = usePathname();
  const { role, setRole } = useDevContext();

  const isAdmin = role === "admin" || role === "lawyer";
  const navItems = isAdmin ? ADMIN_NAV : NEW_HIRE_NAV;

  const isActive = (href: string) =>
    href === "/dashboard" || href === "/onboarding"
      ? pathname === href
      : pathname.startsWith(href);

  return (
    <aside className="w-60 min-h-screen bg-[#0A1020] border-r border-[#1E2D4A] flex flex-col shrink-0">
      <div className="px-6 py-6">
        <span
          className="text-[#C9A84C] font-[family-name:var(--font-playfair)] text-xl font-semibold tracking-wide"
        >
          LexOnboard
        </span>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-1">
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors",
                active
                  ? "border-l-2 border-[#C9A84C] pl-[10px] bg-[#1A2540] text-[#F5F3EE]"
                  : "text-[#8899BB] hover:bg-[#131E33] hover:text-[#F5F3EE]",
              ].join(" ")}
            >
              <span className={active ? "text-[#C9A84C]" : ""}>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {process.env.NODE_ENV === "development" && (
        <div className="px-4 pb-6 space-y-2">
          <span className="block text-[10px] font-semibold text-orange-400 tracking-widest uppercase">
            Dev Mode
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setRole("admin")}
              className={[
                "flex-1 text-xs py-1.5 rounded border transition-colors",
                role === "admin" || role === "lawyer"
                  ? "border-[#C9A84C] text-[#C9A84C] bg-[#C9A84C]/10"
                  : "border-[#1E2D4A] text-[#64748B] hover:border-[#C9A84C]/50",
              ].join(" ")}
            >
              Admin
            </button>
            <button
              onClick={() => setRole("new_hire")}
              className={[
                "flex-1 text-xs py-1.5 rounded border transition-colors",
                role === "new_hire"
                  ? "border-[#C9A84C] text-[#C9A84C] bg-[#C9A84C]/10"
                  : "border-[#1E2D4A] text-[#64748B] hover:border-[#C9A84C]/50",
              ].join(" ")}
            >
              New Hire
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
