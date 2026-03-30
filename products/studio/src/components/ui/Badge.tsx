interface BadgeProps {
  label: string;
  variant?: "default" | "blue" | "green" | "red" | "yellow" | "gray" | "purple" | "mint";
  size?: "sm" | "md";
}

const variants: Record<string, string> = {
  default: "bg-nagarro-gray-100 text-nagarro-blue-700 dark:bg-nagarro-blue-700/30 dark:text-nagarro-gray-300",
  blue: "bg-nagarro-blue-700/10 text-nagarro-blue-700 dark:bg-nagarro-blue-700/30 dark:text-nagarro-gray-300",
  green: "bg-nagarro-green-100 text-nagarro-green-900 dark:bg-nagarro-green-900/30 dark:text-nagarro-green-300",
  red: "bg-nagarro-pink-100 text-nagarro-pink-500 dark:bg-nagarro-pink-900/30 dark:text-nagarro-pink-300",
  yellow: "bg-nagarro-yellow-100 text-nagarro-yellow-700 dark:bg-nagarro-yellow-700/20 dark:text-nagarro-yellow-300",
  gray: "bg-nagarro-gray-100 text-nagarro-blue-500 dark:bg-nagarro-blue-500/20 dark:text-nagarro-gray-400",
  purple: "bg-nagarro-purple-300/30 text-nagarro-purple-700 dark:bg-nagarro-purple-900/30 dark:text-nagarro-purple-300",
  mint: "bg-nagarro-green-100 text-nagarro-green-700 dark:bg-nagarro-green-700/20 dark:text-nagarro-green-300",
};

export function Badge({ label, variant = "default", size = "sm" }: BadgeProps) {
  const sz = size === "sm" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2.5 py-1";
  return (
    <span className={`inline-flex items-center rounded font-medium ${sz} ${variants[variant]}`}>
      {label}
    </span>
  );
}

export function ImpactBadge({ direction }: { direction?: string }) {
  if (direction === "maximize") return <Badge label="maximize" variant="green" />;
  if (direction === "minimize") return <Badge label="minimize" variant="red" />;
  return null;
}

export function StatusBadge({ status }: { status?: string }) {
  const map: Record<string, BadgeProps["variant"]> = {
    active: "green",
    draft: "blue",
    deprecated: "gray",
    proposed: "yellow",
  };
  return <Badge label={status ?? "unknown"} variant={map[status ?? ""] ?? "gray"} />;
}

export function QualityBadge({ score }: { score?: number }) {
  if (score === undefined || score === null) return null;
  const pct = Math.round(score * 100);
  const variant: BadgeProps["variant"] = pct >= 80 ? "green" : pct >= 50 ? "yellow" : "red";
  return <Badge label={`${pct}%`} variant={variant} />;
}
