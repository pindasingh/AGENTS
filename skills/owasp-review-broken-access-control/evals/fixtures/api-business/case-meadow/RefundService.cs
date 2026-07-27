public sealed class RefundService(ICreditLedger credits)
{
    public bool UpdateDraft(Actor actor, Refund refund, EditableRefundPatch patch)
    {
        if (!actor.Authenticated || actor.Tenant != refund.Tenant || refund.Status != "draft") return false;
        refund.Amount = patch.Amount;
        refund.Reason = patch.Reason;
        return true;
    }

    public bool Approve(Actor actor, Refund refund)
    {
        if (!actor.Authenticated || actor.Role != "Manager" || actor.Tenant != refund.Tenant) return false;

        lock (refund)
        {
            if (refund.Status != "reviewed" || refund.CreditIssued) return false;
            credits.Issue(refund.Id, refund.Amount);
            refund.CreditIssued = true;
            refund.ApprovedBy = actor.Id;
            refund.Status = "approved";
            return true;
        }
    }
}

public interface ICreditLedger
{
    void Issue(string refundId, decimal amount);
}
