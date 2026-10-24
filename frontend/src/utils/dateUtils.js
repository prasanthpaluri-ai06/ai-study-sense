/**
 * Central Date & Time Utility for AI StudySense
 * Single source of truth for all timezone conversions, real-time clock synchronization,
 * calendar date math, and human-friendly formatting.
 * Default application timezone: Asia/Kolkata
 */

export const DEFAULT_TIMEZONE = "Asia/Kolkata";

/**
 * Detects the user's local timezone name, defaulting to Asia/Kolkata.
 */
export function getUserTimeZone() {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return tz || DEFAULT_TIMEZONE;
  } catch (e) {
    return DEFAULT_TIMEZONE;
  }
}

/**
 * Returns today's calendar date as 'YYYY-MM-DD' in the user's local timezone.
 */
export function getTodayDateString(d = new Date()) {
  const dateObj = typeof d === "string" ? new Date(d) : d;
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, "0");
  const day = String(dateObj.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Converts a Date object into a local 'YYYY-MM-DDTHH:mm' string suitable for
 * <input type="datetime-local" /> without UTC skew.
 */
export function toLocalDateTimeInputValue(d = new Date()) {
  const dateObj = typeof d === "string" ? new Date(d) : d;
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, "0");
  const day = String(dateObj.getDate()).padStart(2, "0");
  const hours = String(dateObj.getHours()).padStart(2, "0");
  const minutes = String(dateObj.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Parses an input value from <input type="datetime-local" /> and returns an ISO string
 * preserving the exact chosen local time.
 */
export function toIsoFromLocalInput(localInputStr) {
  if (!localInputStr) return null;
  const d = new Date(localInputStr);
  return isNaN(d.getTime()) ? null : d.toISOString();
}

/**
 * Formats a date string into readable date (e.g., 'Oct 10, 2026').
 */
export function formatDate(dateVal, options = {}) {
  if (!dateVal) return "";
  const d = typeof dateVal === "string" ? new Date(dateVal) : dateVal;
  if (isNaN(d.getTime())) return String(dateVal);

  const defaultOptions = {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: getUserTimeZone(),
    ...options,
  };

  return new Intl.DateTimeFormat("en-US", defaultOptions).format(d);
}

/**
 * Formats a date string into readable date & time (e.g., 'Oct 10, 2026, 3:30 PM').
 */
export function formatDateTime(dateVal, options = {}) {
  if (!dateVal) return "";
  const d = typeof dateVal === "string" ? new Date(dateVal) : dateVal;
  if (isNaN(d.getTime())) return String(dateVal);

  const defaultOptions = {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: getUserTimeZone(),
    ...options,
  };

  return new Intl.DateTimeFormat("en-US", defaultOptions).format(d);
}

/**
 * Formats time only (e.g. '03:30 PM' or '15:30:00').
 */
export function formatTime(dateVal, includeSeconds = false) {
  if (!dateVal) return "";
  const d = typeof dateVal === "string" ? new Date(dateVal) : dateVal;
  if (isNaN(d.getTime())) return "";

  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: includeSeconds ? "2-digit" : undefined,
    timeZone: getUserTimeZone(),
  }).format(d);
}

/**
 * Calculates human-readable relative deadline / time description (e.g., 'Due in 2 days', 'Overdue by 3h').
 */
export function getRelativeTimeDescription(targetDateVal, now = new Date()) {
  if (!targetDateVal) return "";
  const target = typeof targetDateVal === "string" ? new Date(targetDateVal) : targetDateVal;
  if (isNaN(target.getTime())) return "";

  const diffMs = target.getTime() - now.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMs < 0) {
    const overdueHours = Math.abs(diffHours);
    if (overdueHours >= 24) {
      const days = Math.floor(overdueHours / 24);
      return `Overdue by ${days}d ${Math.floor(overdueHours % 24)}h`;
    }
    return `Overdue by ${Math.max(1, Math.floor(overdueHours))}h`;
  }

  if (diffHours < 1) {
    const mins = Math.max(1, Math.floor(diffMs / (1000 * 60)));
    return `Due in ${mins} minute${mins === 1 ? "" : "s"}`;
  }

  if (diffHours < 24) {
    return `Due in ${Math.floor(diffHours)} hours`;
  }

  if (diffDays === 1) {
    return "Due tomorrow";
  }

  return `Due in ${diffDays} days`;
}

/**
 * Checks if a given date string or Date is today in the user's local timezone.
 */
export function isTodayDate(dateVal) {
  if (!dateVal) return false;
  const d = typeof dateVal === "string" ? new Date(dateVal) : dateVal;
  if (isNaN(d.getTime())) return false;
  return getTodayDateString(d) === getTodayDateString(new Date());
}
