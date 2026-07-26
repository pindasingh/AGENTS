public sealed class InvoiceService(AppDbContext db, IAuthorizationService authorization)
{
    public async Task<InvoiceDto> GetAuthorizedInvoice(ClaimsPrincipal subject, string invoiceId)
    {
        var tenantId = subject.RequireTenantId();
        var subjectId = subject.RequireSubjectId();
        var invoice = await db.Invoices.SingleOrDefaultAsync(x =>
            x.Id == invoiceId && x.TenantId == tenantId && x.OwnerId == subjectId);
        if (invoice is null) throw new NotFoundException();
        var decision = await authorization.AuthorizeAsync(subject, invoice, "InvoiceReader");
        if (!decision.Succeeded) throw new ForbiddenException();
        return InvoiceDto.FromAuthorized(invoice);
    }
}
