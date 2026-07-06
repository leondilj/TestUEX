import type { Metadata } from "next";

import { AssistantView } from "./assistant-view";

export const metadata: Metadata = {
  title: "Assistente — Taskly",
};

export default function AssistantPage() {
  return <AssistantView />;
}
