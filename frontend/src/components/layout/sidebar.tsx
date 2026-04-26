"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { useAuth } from "@/lib/hooks/use-auth";
import { cn } from "@/lib/utils";
import { BarChart3, Disc3, ListChecks, Palette, Settings, Smile, Wallet, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

const NAV_ITEMS = [
  { href: "/", icon: Disc3, labelKey: "home" as const },
  { href: "/dashboard", icon: BarChart3, labelKey: "dashboard" as const },
  { href: "/chores", icon: ListChecks, labelKey: "chores" as const },
  { href: "/bucket", icon: Palette, labelKey: "bucket" as const },
  { href: "/happy-bucket", icon: Smile, labelKey: "happyBucket" as const },
  { href: "/wallet", icon: Wallet, labelKey: "wallet" as const },
  { href: "/settings", icon: Settings, labelKey: "settings" as const },
];

export function Sidebar() {
  const t = useTranslations("navigation");
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-card border-r border-border h-full">
      <div className="p-6">
        <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          MeryGoRound
        </h1>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <item.icon className="size-5" />
              {t(item.labelKey)}
            </Link>
          );
        })}
      </nav>

      <Separator />

      <div className="p-4 space-y-3">
        {user && (
          <p className="text-sm font-medium text-foreground truncate px-1">{user.name}</p>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive"
          onClick={logout}
        >
          <LogOut className="size-4" />
          {t("logout")}
        </Button>
      </div>
    </aside>
  );
}
