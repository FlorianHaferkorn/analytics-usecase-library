import { ReactNode, ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children: ReactNode;
}

const variants: Record<string, string> = {
  primary: "bg-brand-mint text-brand-petrol hover:bg-nagarro-green-300 disabled:opacity-50",
  secondary: "bg-theme text-theme border border-theme hover:bg-theme-tertiary disabled:opacity-50",
  ghost: "text-theme-secondary hover:bg-theme-tertiary disabled:opacity-50",
  danger: "bg-nagarro-pink-400 text-white hover:bg-nagarro-pink-500 disabled:opacity-50",
};

const sizes: Record<string, string> = {
  sm: "text-xs px-2.5 py-1.5 rounded",
  md: "text-sm px-4 py-2 rounded-md",
  lg: "text-base px-6 py-3 rounded-lg",
};

export function Button({
  variant = "primary",
  size = "md",
  loading,
  children,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center gap-2 font-medium transition-colors cursor-pointer
        ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled ?? loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}
