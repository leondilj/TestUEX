// Marca do Taskly: check em SVG inline + wordmark minúsculo em Space Grotesk
// (ux-spec-navigation-and-identity.md §3 — sem asset externo)

const SIZES = {
  md: { icon: 20, text: "text-xl" },
  lg: { icon: 26, text: "text-3xl" },
} as const;

export function Logo({ size = "md" }: { size?: keyof typeof SIZES }) {
  const { icon, text } = SIZES[size];
  return (
    <span className="inline-flex items-center gap-1.5">
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
        className="text-accent"
      >
        <path
          d="M4 13l5 5L20 6"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className={`font-display font-semibold lowercase ${text}`}>
        taskly
      </span>
    </span>
  );
}
