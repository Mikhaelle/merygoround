"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { cn } from "@/lib/utils";
import { BarChart3, Disc3, ListChecks, Palette, Settings, Smile, Wallet } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", icon: Disc3, labelKey: "home" as const },
  { href: "/dashboard", icon: BarChart3, labelKey: "dashboard" as const },
  { href: "/chores", icon: ListChecks, labelKey: "chores" as const },
  { href: "/bucket", icon: Palette, labelKey: "bucket" as const },
  { href: "/happy-bucket", icon: Smile, labelKey: "happyBucket" as const },
  { href: "/wallet", icon: Wallet, labelKey: "wallet" as const },
  { href: "/settings", icon: Settings, labelKey: "settings" as const },
];

export function MobileNav() {
  const t = useTranslations("navigation");
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-card/95 backdrop-blur-lg lg:hidden">
      <div className="flex items-center justify-around h-16">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center gap-1 px-3 py-2 text-xs font-medium transition-colors",
                isActive
                  ? "text-indigo-600 dark:text-indigo-400"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <item.icon
                className={cn(
                  "size-5 transition-transform",
                  isActive && "scale-110",
                )}
              />
              <span>{t(item.labelKey)}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
