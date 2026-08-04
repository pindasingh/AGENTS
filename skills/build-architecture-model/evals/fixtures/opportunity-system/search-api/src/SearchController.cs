[ApiController]
public sealed class SearchController : ControllerBase
{
    [HttpPost("/api/opportunities/search")]
    [ContractVersion("v2")]
    public async Task<SearchResponseV2> Search(SearchRequestV2 request)
    {
        var result = await mediator.Send(new SearchQuery(request));
        return mapper.Map<SearchResponseV2>(result);
    }
}
