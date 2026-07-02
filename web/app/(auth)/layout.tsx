"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Logo } from "@/components/ui/logo";
import { useSession } from "@/lib/use-session";

// Layout (auth): card centrado sobre fundo paper (T26 §6).
// Usuário já logado não vê login/cadastro — vai direto para /projects (T26 §4)
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { data: user } = useSession();

  useEffect(() => {
    if (user) router.replace("/projects");
  }, [user, router]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 px-4 py-12">
      <Logo size="lg" />
      <main className="w-full max-w-sm rounded-[10px] border border-line bg-surface p-6 shadow-sm">
        {children}
      </main>
    </div>
  );
}
