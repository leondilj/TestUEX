"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Logo } from "@/components/ui/logo";
import { useSession } from "@/lib/use-session";

// Raiz: decide o destino pela sessão (ux-spec-navigation-and-identity.md §4)
// — com sessão vai para /projects, sem sessão para /login
export default function Home() {
  const router = useRouter();
  const { data: user, isPending } = useSession();

  useEffect(() => {
    if (isPending) return;
    router.replace(user ? "/projects" : "/login");
  }, [isPending, user, router]);

  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="animate-pulse" aria-hidden="true">
        <Logo size="lg" />
      </div>
    </div>
  );
}
