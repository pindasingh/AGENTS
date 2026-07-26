var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddJwtBearer();
builder.Services.AddAuthorization(options =>
    options.AddPolicy("Orders.Read", policy =>
        policy.RequireAuthenticatedUser().RequireRole("Orders.Application")));
builder.Services.AddScoped<OrderReader>();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
app.Run();
