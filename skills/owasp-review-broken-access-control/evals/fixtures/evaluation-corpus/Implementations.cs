public sealed record Attempt(bool Authenticated, string ActorId, string ActorTenant, string OwnerId, string ResourceTenant);

public static class Quartz
{
    public static bool IsAllowed(Attempt attempt) => attempt.Authenticated;
}

public static class Nimbus
{
    public static bool IsAllowed(Attempt attempt) =>
        attempt.Authenticated && attempt.ActorTenant == attempt.ResourceTenant;
}
