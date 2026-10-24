import React from "react";

export default function Button({
  children,
  variant = "primary", // primary, secondary, outline, ghost
  size = "md", // sm, md, lg
  icon: Icon,
  disabled = false,
  loading = false,
  type = "button",
  onClick,
  style = {},
  className = "",
}) {
  let variantClass = "btn-primary";
  if (variant === "secondary") variantClass = "btn-secondary";
  else if (variant === "outline") variantClass = "btn-outline";
  else if (variant === "ghost") variantClass = "btn-ghost";

  let sizeStyle = {};
  if (size === "sm") {
    sizeStyle = { padding: "0.35rem 0.7rem", fontSize: "0.82rem" };
  } else if (size === "lg") {
    sizeStyle = { padding: "0.75rem 1.5rem", fontSize: "1rem" };
  }

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`btn ${variantClass} ${className}`}
      style={{
        opacity: disabled ? 0.6 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
        ...sizeStyle,
        ...style,
      }}
    >
      {loading ? (
        <span style={{ display: "inline-block", animation: "spin 1s linear infinite" }}>⏳</span>
      ) : Icon ? (
        <Icon size={size === "sm" ? 14 : 16} />
      ) : null}
      <span>{children}</span>
    </button>
  );
}
