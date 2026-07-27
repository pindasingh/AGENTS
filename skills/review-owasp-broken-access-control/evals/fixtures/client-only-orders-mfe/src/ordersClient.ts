export async function getOrder(orderId: string, accessToken: string) {
  return fetch(`/api/orders/${encodeURIComponent(orderId)}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export async function approveOrder(orderId: string, accessToken: string) {
  return fetch(`/api/orders/${encodeURIComponent(orderId)}/approve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}
