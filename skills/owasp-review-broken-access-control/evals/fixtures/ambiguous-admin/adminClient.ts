export const canSeeRefundApproval = (claims: { roles: string[] }) =>
  claims.roles.includes("Admin");
