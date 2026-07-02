// Datas sempre em pt-BR (ux-spec-navigation-and-identity.md §3).
// A API trafega ISO 8601 UTC; a conversão para exibição acontece aqui.

const DATE_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export function formatDate(iso: string): string {
  return DATE_FORMATTER.format(new Date(iso));
}
