"use client";

import { useState, useEffect } from "react";
import { Moon, Sun, Bell, Lock, User, Mail, Shield } from "lucide-react";
import { toast } from "sonner";

function SectionHeader({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="flex items-start gap-3 pb-4 border-b border-[#1E2D4A]">
      <div className="mt-0.5 text-[#C9A84C]">{icon}</div>
      <div>
        <p className="text-sm font-semibold text-[#F5F3EE]">{title}</p>
        <p className="text-xs text-[#64748B] mt-0.5">{description}</p>
      </div>
    </div>
  );
}

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={[
        "relative w-10 h-5 rounded-full transition-colors shrink-0",
        enabled ? "bg-[#C9A84C]" : "bg-[#1E2D4A]",
      ].join(" ")}
    >
      <span
        className={[
          "absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform",
          enabled ? "translate-x-5" : "translate-x-0.5",
        ].join(" ")}
      />
    </button>
  );
}

function FieldRow({ label, note, children }: { label: string; note?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-4 border-b border-[#1E2D4A] last:border-0">
      <div className="min-w-0 mr-4">
        <p className="text-sm text-[#F5F3EE]">{label}</p>
        {note && <p className="text-xs text-[#64748B] mt-0.5">{note}</p>}
      </div>
      {children}
    </div>
  );
}

type Theme = "dark" | "light";

export default function SettingsPage() {
  const [theme, setTheme] = useState<Theme>("dark");
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [inAppNotifs, setInAppNotifs] = useState(true);
  const [displayName, setDisplayName] = useState("Admin User");
  const [email, setEmail] = useState("admin@yourorg.com");
  const [nameDirty, setNameDirty] = useState(false);
  const [emailDirty, setEmailDirty] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("lex-theme") as Theme | null;
    if (stored) setTheme(stored);
    const en = localStorage.getItem("lex-email-notifs");
    if (en !== null) setEmailNotifs(en === "true");
    const ian = localStorage.getItem("lex-inapp-notifs");
    if (ian !== null) setInAppNotifs(ian === "true");
  }, []);

  function handleTheme(t: Theme) {
    setTheme(t);
    localStorage.setItem("lex-theme", t);
    if (t === "light") {
      toast.info("Light mode coming soon — saved your preference");
    } else {
      toast.success("Dark mode applied");
    }
  }

  function handleEmailNotifs(v: boolean) {
    setEmailNotifs(v);
    localStorage.setItem("lex-email-notifs", String(v));
    toast.success(v ? "Email notifications enabled" : "Email notifications disabled");
  }

  function handleInAppNotifs(v: boolean) {
    setInAppNotifs(v);
    localStorage.setItem("lex-inapp-notifs", String(v));
    toast.success(v ? "In-app notifications enabled" : "In-app notifications disabled");
  }

  function handleSaveProfile() {
    setNameDirty(false);
    setEmailDirty(false);
    toast.success("Profile saved — will sync once authentication is set up");
  }

  return (
    <div className="max-w-2xl space-y-10">
      <div>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE] mb-2">
          Settings
        </h1>
        <p className="text-[#64748B]">Manage your account, appearance, and preferences</p>
      </div>

      {/* Appearance */}
      <div className="space-y-4">
        <SectionHeader
          icon={<Sun size={16} />}
          title="Appearance"
          description="Choose how LexOnBoard looks"
        />
        <div className="flex gap-3">
          {(["dark", "light"] as Theme[]).map((t) => (
            <button
              key={t}
              onClick={() => handleTheme(t)}
              className={[
                "flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border text-sm font-medium transition-colors",
                theme === t
                  ? "border-[#C9A84C] bg-[#C9A84C]/10 text-[#C9A84C]"
                  : "border-[#1E2D4A] text-[#64748B] hover:border-[#C9A84C]/40 hover:text-[#F5F3EE]",
              ].join(" ")}
            >
              {t === "dark" ? <Moon size={15} /> : <Sun size={15} />}
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Profile */}
      <div className="space-y-4">
        <SectionHeader
          icon={<User size={16} />}
          title="Profile"
          description="Your display name and email address"
        />
        <div className="border border-[#1E2D4A] rounded-lg px-5">
          <FieldRow label="Display name" note="Shown across the platform">
            <input
              type="text"
              value={displayName}
              onChange={(e) => { setDisplayName(e.target.value); setNameDirty(true); }}
              className="w-48 bg-[#0D1829] border border-[#1E2D4A] rounded px-3 py-1.5 text-sm text-[#F5F3EE] focus:outline-none focus:border-[#C9A84C]/50"
            />
          </FieldRow>
          <FieldRow label="Email" note="Used for notifications and login">
            <div className="flex items-center gap-2">
              <Mail size={13} className="text-[#64748B] shrink-0" />
              <input
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setEmailDirty(true); }}
                className="w-48 bg-[#0D1829] border border-[#1E2D4A] rounded px-3 py-1.5 text-sm text-[#F5F3EE] focus:outline-none focus:border-[#C9A84C]/50"
              />
            </div>
          </FieldRow>
        </div>
        {(nameDirty || emailDirty) && (
          <button
            onClick={handleSaveProfile}
            className="px-4 py-2 bg-[#C9A84C] text-[#0F1729] rounded-md text-sm font-semibold hover:bg-[#B8963E] transition-colors"
          >
            Save Changes
          </button>
        )}
      </div>

      {/* Security */}
      <div className="space-y-4">
        <SectionHeader
          icon={<Lock size={16} />}
          title="Security"
          description="Password and account access"
        />
        <div className="border border-[#1E2D4A] rounded-lg px-5">
          <FieldRow label="Password" note="Change your account password">
            <button
              disabled
              className="px-4 py-1.5 border border-[#1E2D4A] rounded text-sm text-[#64748B] cursor-not-allowed opacity-50"
              title="Requires authentication to be set up"
            >
              Change password
            </button>
          </FieldRow>
          <FieldRow label="Two-factor authentication" note="Add an extra layer of security">
            <button
              disabled
              className="px-4 py-1.5 border border-[#1E2D4A] rounded text-sm text-[#64748B] cursor-not-allowed opacity-50"
            >
              Enable 2FA
            </button>
          </FieldRow>
        </div>
        <div className="flex items-center gap-2 text-xs text-[#64748B]">
          <Shield size={12} />
          <span>Security features available once Supabase authentication is connected</span>
        </div>
      </div>

      {/* Notifications */}
      <div className="space-y-4">
        <SectionHeader
          icon={<Bell size={16} />}
          title="Notifications"
          description="Control how you receive updates"
        />
        <div className="border border-[#1E2D4A] rounded-lg px-5">
          <FieldRow label="Email notifications" note="Playbook updates, processing complete">
            <Toggle enabled={emailNotifs} onChange={handleEmailNotifs} />
          </FieldRow>
          <FieldRow label="In-app notifications" note="Toast alerts and status updates">
            <Toggle enabled={inAppNotifs} onChange={handleInAppNotifs} />
          </FieldRow>
        </div>
      </div>
    </div>
  );
}
