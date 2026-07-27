public sealed record Actor(string Id, string Tenant, string Role, bool Authenticated);
public sealed record EditableRefundPatch(decimal Amount, string Reason);

public sealed class Refund
{
    public required string Id { get; init; }
    public required string Tenant { get; init; }
    public string Status { get; set; } = "draft";
    public string? ApprovedBy { get; set; }
    public bool CreditIssued { get; set; }
    public decimal Amount { get; set; }
    public string Reason { get; set; } = "";
}
