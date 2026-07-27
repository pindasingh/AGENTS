public sealed class RefundService(ICreditLedger credits)
{
    public bool Update(Actor actor, Refund refund, RefundPatch patch)
    {
        if (!actor.Authenticated || actor.Tenant != refund.Tenant) return false;

        refund.Amount = patch.Amount;
        refund.Reason = patch.Reason;
        refund.Status = patch.Status ?? refund.Status;
        refund.ApprovedBy = patch.ApprovedBy ?? refund.ApprovedBy;

        if (refund.Status == "approved" && !refund.CreditIssued)
        {
            credits.Issue(refund.Id, refund.Amount);
            refund.CreditIssued = true;
        }

        return true;
    }
}

public interface ICreditLedger
{
    void Issue(string refundId, decimal amount);
}
