public sealed record Challenge(string Id, string Policy);

public static class ChallengeCatalog
{
    public static readonly Challenge[] All =
    [
        new("Quartz", "An authenticated user may read only records they own."),
        new("Nimbus", "An authenticated user may read only resources in their identity-bound tenant.")
    ];
}
