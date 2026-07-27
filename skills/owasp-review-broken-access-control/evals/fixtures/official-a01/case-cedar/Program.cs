using System.Security.Claims;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddBearerToken();
builder.Services.AddAuthorization();
builder.Services.AddSingleton<AccountStore>();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/account", (string acct, ClaimsPrincipal user, AccountStore accounts) =>
{
    var subject = user.FindFirstValue("sub");
    if (subject is null) return Results.Forbid();

    var account = accounts.FindForOwner(acct, subject);
    return account is null ? Results.NotFound() : Results.Ok(account);
}).RequireAuthorization();

app.Run();
