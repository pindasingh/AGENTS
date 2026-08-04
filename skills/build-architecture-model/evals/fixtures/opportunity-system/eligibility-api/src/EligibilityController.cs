[HttpPost("/api/v2/eligibility/check")]
[Contract("EligibilityCheckV2", Fingerprint = "sha256:eligibility-v2")]
public EligibilityResultV2 Check(EligibilityRequestV2 request) => rules.Evaluate(request);
