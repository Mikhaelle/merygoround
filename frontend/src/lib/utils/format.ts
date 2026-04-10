/** Format an ISO date string to a localized short date. */
export function formatDate(isoString: string, locale: string = "en"): string {
  const date = new Date(isoString);
  return date.toLocaleDateString(locale === "pt-BR" ? "pt-BR" : "en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Format an ISO date string to a localized date with time. */
export function formatDateTime(isoString: string, locale: string = "en"): string {
  const date = new Date(isoString);
  return date.toLocaleDateString(locale === "pt-BR" ? "pt-BR" : "en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Format a duration in minutes into a human-readable string. */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
}

/** Format an hour number (0-23) to a display string. */
export function formatHour(hour: number): string {
  return `${hour.toString().padStart(2, "0")}:00`;
}

/** Format a value as BRL currency using pt-BR locale (e.g. R$ 1,00). */
export function formatBRL(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}
