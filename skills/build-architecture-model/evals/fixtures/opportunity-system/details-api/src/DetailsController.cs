[HttpPost("/api/v2/opportunities/details")]
[Contract("OpportunityDetailsV2", Fingerprint = "sha256:details-v2")]
public DetailsResultV2 Get(DetailsRequestV2 request) => repository.Read(request.Ids);
