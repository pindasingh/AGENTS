public class AuthorizationTests
{
    [Fact] public Task OwnerCanReadInvoice() => AssertAllowed("alice", "tenant-a", "invoice-alice");
    [Fact] public Task PeerCannotReadInvoice() => AssertNoDataOrSideEffect("bob", "tenant-a", "invoice-alice");
    [Fact] public Task OtherTenantCannotReadInvoice() => AssertNoDataOrSideEffect("mallory", "tenant-b", "invoice-alice");
    [Fact] public Task OrdinaryUserCannotApproveRefund() => AssertDeniedAndUnchanged("alice", "refund-1");
    [Fact] public Task RevokedSessionCannotReadInvoice() => AssertDeniedAfterLogout("alice", "invoice-alice");
    [Fact] public Task AlternateMethodsAreRejected() => AssertMethodsRejected("/api/invoices/invoice-alice", "POST", "PUT", "DELETE");
}
