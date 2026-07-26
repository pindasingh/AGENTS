var builder = WebApplication.CreateBuilder(args);

builder.Services.AddAuthorization(options =>
{
    options.FallbackPolicy = new AuthorizationPolicyBuilder()
        .RequireAuthenticatedUser()
        .Build();
    options.AddPolicy("RefundApprover", policy => policy.RequireRole("refund-approver"));
});

builder.Services.AddCors(options => options.AddPolicy("BrowserClient", policy =>
    policy.WithOrigins("https://app.example.test")
          .WithMethods("GET", "POST")
          .AllowCredentials()));

var app = builder.Build();
app.UseCors("BrowserClient");
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/api/invoices/{invoiceId}", async (
    string invoiceId, ClaimsPrincipal user, InvoiceService invoices) =>
    await invoices.GetAuthorizedInvoice(user, invoiceId));

app.MapPost("/api/refunds/{refundId}/approve", async (
    string refundId, ClaimsPrincipal user, RefundService refunds) =>
    await refunds.ApproveForAuthorizedTenant(user, refundId))
    .RequireAuthorization("RefundApprover");

app.MapPost("/api/logout", async (HttpContext context, SessionRegistry sessions) =>
{
    await sessions.Revoke(context.User, context.TraceIdentifier);
    await context.SignOutAsync();
}).RequireAuthorization();

app.Run();
