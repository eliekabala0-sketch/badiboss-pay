export function formatMoney(value: number | string | null | undefined, currency = "UNKNOWN") {
  if (value === null || value === undefined) return "N/A";
  const numberValue = Number(value);
  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(numberValue) + ` ${currency || "UNKNOWN"}`;
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function statusLabel(value: string | boolean | null | undefined) {
  if (typeof value === "boolean") return value ? "Actif" : "Inactif";
  const labels: Record<string, string> = {
    active: "Actif",
    inactive: "Inactif",
    suspended: "Suspendu",
    pending: "En attente",
    success: "success / paye",
    completed: "Termine",
    paid: "Paye",
    failed: "Echoue",
    error: "Erreur",
    expired: "Expire",
    trial: "Essai gratuit",
  };
  return labels[String(value ?? "").toLowerCase()] ?? (value || "-");
}

export function appTypeLabel(value: string) {
  const labels: Record<string, string> = {
    saas: "SaaS abonnement",
    training: "Formation",
    restaurant: "Restaurant",
    church: "Eglise",
    discovery: "Decouverte",
    marketplace: "Marketplace",
    other: "Autre",
  };
  return labels[value] ?? value;
}

export function commissionLabel(value: string) {
  const labels: Record<string, string> = {
    fixed: "Fixe",
    percentage: "Pourcentage",
    none: "Aucune",
  };
  return labels[value] ?? value;
}

export function planLabel(value: string) {
  const labels: Record<string, string> = {
    monthly: "Mensuel",
    quarterly: "Trimestriel",
    yearly: "Annuel",
    trial: "Essai gratuit",
  };
  return labels[value] ?? value;
}
