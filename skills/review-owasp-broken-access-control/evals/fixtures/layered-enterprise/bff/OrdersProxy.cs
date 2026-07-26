[Authorize]
public sealed class OrdersProxy(
    IHttpClientFactory clients,
    IApplicationTokenProvider tokens,
    IConfiguration configuration)
{
    public async Task<HttpResponseMessage> GetOrder(
        ClaimsPrincipal browserUser,
        string orderId,
        CancellationToken cancellationToken)
    {
        var request = new HttpRequestMessage(HttpMethod.Get, $"/orders/{orderId}");
        request.Headers.Authorization = new("Bearer", await tokens.GetClientCredentialsToken("orders-api"));
        request.Headers.Add("Ocp-Apim-Subscription-Key", configuration["Orders:SubscriptionKey"]);
        request.Headers.Add("X-Partner-Channel", "orders-bff");
        // The browser user's subject, tenant, and supplier assignment are not propagated.
        return await clients.CreateClient("OrdersApim").SendAsync(request, cancellationToken);
    }
}
