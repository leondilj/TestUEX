import type { Metadata } from "next";
import { Suspense } from "react";

import { LoginForm } from "./login-form";

export const metadata: Metadata = {
  title: "Entrar — Taskly",
};

export default function LoginPage() {
  // Suspense exigido pelo useSearchParams do form durante o prerender
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
