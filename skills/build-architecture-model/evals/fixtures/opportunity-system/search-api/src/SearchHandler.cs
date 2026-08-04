public sealed class SearchHandler
{
    public async Task<SearchResult> Handle(SearchQuery query)
    {
        if (!await flags.BoolVariationAsync("new-opportunity-search", query.UserId))
            return SearchResult.Disabled();
        var maximum = options.Value.MaximumResults;
        var hits = await elastic.SearchAsync(query.Term, maximum);
        var profile = await db.Profiles.SingleAsync(query.UserId);
        var eligible = await eligibility.CheckV2(query.UserId, hits.Ids);
        var details = await details.GetV2(eligible.Ids);
        telemetry.TrackEvent("OpportunitySearchCompleted");
        return SearchResult.From(details, profile);
    }
}
