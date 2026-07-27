var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddBearerToken();
builder.Services.AddAuthorization();
builder.Services.AddSingleton<AccountStore>();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/account", (string acct, AccountStore accounts) =>
{
    var account = accounts.Find(acct);
    return account is null ? Results.NotFound() : Results.Ok(account);
}).RequireAuthorization();

app.Run();
