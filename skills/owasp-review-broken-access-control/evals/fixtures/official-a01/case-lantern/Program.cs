var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddBearerToken();
builder.Services.AddAuthorization(options =>
{
    options.FallbackPolicy = new AuthorizationPolicyBuilder()
        .RequireAuthenticatedUser()
        .Build();
    options.AddPolicy("AdminOnly", policy => policy.RequireRole("Admin"));
});

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/app/getappInfo", () => Results.Ok(new { version = "1.0" }));
app.MapGet("/app/admin_getappInfo", () => Results.Ok(new { diagnostics = "internal" }))
    .RequireAuthorization("AdminOnly");

app.Run();
