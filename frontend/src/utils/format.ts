export function formatMoney(value: number | string | null | undefined, currency = "CDF") {
  const numberValue = Number(value ?? 0);
  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(numberValue) + ` ${currency}`;
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
    success: "Réussi",
    completed: "Terminé",
    paid: "Payé",
    failed: "Échoué",
    error: "Erreur",
    expired: "Expiré",
    trial: "Essai gratuit",
  };
  return labels[String(value ?? "").toLowerCase()] ?? (value || "-");
}

export function appTypeLabel(value: string) {
  const labels: Record<string, string> = {
    saas: "SaaS abonnement",
    training: "Formation",
    restaurant: "Restaurant",
    church: "Église",
    discovery: "Découverte",
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
