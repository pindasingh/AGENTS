type User = { roles: string[] };

export function visibleRoutes(user: User) {
  return [
    { path: "/orders", visible: true },
    { path: "/orders/admin", visible: user.roles.includes("OrdersAdmin") },
  ];
}
