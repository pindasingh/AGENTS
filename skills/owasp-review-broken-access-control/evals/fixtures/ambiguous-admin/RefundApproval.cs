using System.Security.Claims;

public static class RefundsController
{
    public static IResult Approve(string id, ClaimsPrincipal user, RefundStore refunds, RefundApprovalPolicy policy)
    {
        var refund = refunds.Find(id);
        if (refund is null) return Results.NotFound();
        if (!policy.CanApprove(user, refund)) return Results.Forbid();
        refund.Status = "approved";
        return Results.Ok();
    }
}

public sealed class RefundApprovalPolicy
{
    public bool CanApprove(ClaimsPrincipal user, Refund refund) =>
        user.IsInRole("Admin") &&
        user.FindFirst("tenant")?.Value == refund.Tenant &&
        refund.Status == "pending" &&
        refund.AssignedApprover == user.FindFirst("sub")?.Value;
}

public sealed class RefundStore
{
    public Refund? Find(string id) => new()
    {
        Id = id,
        Tenant = "north",
        Status = "pending",
        AssignedApprover = "alice"
    };
}

public sealed class Refund
{
    public required string Id { get; init; }
    public required string Tenant { get; init; }
    public required string AssignedApprover { get; init; }
    public required string Status { get; set; }
}
