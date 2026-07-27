export function renderExport(user: { roles: string[] }) {
  if (!user.roles.includes("Admin")) return null;
  return { label: "Export", action: () => fetch("/admin/export", { method: "POST" }) };
}
