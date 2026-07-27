public sealed record Account(string Id, string OwnerId, decimal Balance);

public sealed class AccountStore
{
    private readonly Account[] accounts =
    [
        new("acct-101", "alice", 125m),
        new("acct-202", "bob", 900m)
    ];

    public Account? Find(string id) =>
        accounts.SingleOrDefault(account => account.Id == id);

    public Account? FindForOwner(string id, string ownerId) =>
        accounts.SingleOrDefault(account => account.Id == id && account.OwnerId == ownerId);
}
