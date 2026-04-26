"use client";

import { useAuth } from "@/lib/hooks/use-auth";
import { useRouter } from "@/i18n/navigation";
import { useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { MobileNav } from "@/components/layout/mobile-nav";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

/** Dashboard shell with sidebar, header, and mobile navigation. */
export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((registration) => {
        registration.update().catch(() => {});
        console.info("[merygoround] service worker registered", {
          scope: registration.scope,
          state:
            registration.active?.state ??
            registration.installing?.state ??
            registration.waiting?.state ??
            "unknown",
        });
      })
      .catch((err) => {
        console.error("[merygoround] service worker registration failed", err);
      });
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="size-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto pb-20 lg:pb-6">
          <div className="mx-auto max-w-6xl px-4 py-6">{children}</div>
        </main>
        <MobileNav />
      </div>
    </div>
  );
}
