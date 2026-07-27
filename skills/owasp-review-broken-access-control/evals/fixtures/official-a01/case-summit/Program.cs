var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddBearerToken();
builder.Services.AddAuthorization(options =>
    options.AddPolicy("AdminOnly", policy => policy.RequireRole("Admin")));

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapPost("/admin/export", () => Results.Accepted("/exports/latest"))
    .RequireAuthorization("AdminOnly");

app.Run();
