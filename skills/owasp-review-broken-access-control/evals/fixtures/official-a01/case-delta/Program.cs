var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddBearerToken();
builder.Services.AddAuthorization();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapPost("/admin/export", () => Results.Accepted("/exports/latest"))
    .RequireAuthorization();

app.Run();
