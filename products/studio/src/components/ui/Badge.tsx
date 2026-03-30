interface BadgeProps {
  label: string;
  variant?: "default" | "blue" | "green" | "red" | "yellow" | "gray" | "purple";
  size?: "sm" | "md";
}

const variants: Record<string, string> = {
  default: "bg-slate-100 text-slate-700",
  blue: "bg-blue-100 text-blue-800",
  green: "bg-green-100 text-green-800",
  red: "bg-red-100 text-red-800",
  yellow: "bg-yellow-100 text-yellow-800",
  gray: "bg-gray-100 text-gray-600",
  purple: "bg-purple-100 text-purple-800",
};

export function Badge({ label, variant = "default", size = "sm" }: BadgeProps) {
  const sz = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-2.5 py-1";
  return (
    <span className={`inline-flex items-center rounded-full font-medium ${sz} ${variants[variant]}`}>
      {label}
    </span>
  );
}

export function ImpactBadge({ direction }: { direction?: string }) {
  if (direction === "maximize") return <Badge label="↑ maximize" variant="green" />;
  if (direction === "minimize") return <Badge label="↓ minimize" variant="red" />;
  return null;
}

export function StatusBadge({ status }: { status?: string }) {
  const map: Record<string, "green" | "blue" | "gray"> = {
    active: "green",
    draft: "blue",
    deprecated: "gray",
  };
  return <Badge label={status ?? "unknown"} variant={map[status ?? ""] ?? "gray"} />;
}
