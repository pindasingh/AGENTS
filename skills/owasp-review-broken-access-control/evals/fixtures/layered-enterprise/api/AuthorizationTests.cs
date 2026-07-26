public sealed class AuthorizationTests
{
    [Fact]
    public Task ApplicationRoleCanCallOrdersEndpoint() =>
        AssertAllowedWithApplicationToken("Orders.Application", "order-1");

    // No browser-user, supplier-assignment, peer-order, or cross-tenant test exists.
}
