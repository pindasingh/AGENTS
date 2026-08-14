var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddBearerToken();
builder.Services.AddAuthorization(options =>
    options.FallbackPolicy = new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build());
builder.Services.AddSingleton<RefundStore>();
builder.Services.AddSingleton<RefundApprovalPolicy>();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapPost("/v2/refunds/{id}/approve", RefundsController.Approve);
app.Run();
