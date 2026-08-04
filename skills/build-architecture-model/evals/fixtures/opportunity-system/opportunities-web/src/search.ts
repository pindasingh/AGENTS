// Independently deployed Opportunities web application.
export async function search(request: SearchRequestV2): Promise<SearchResponseV2> {
  return fetch("https://opportunity-search/api/opportunities/search", {
    method: "POST",
    headers: {"content-type": "application/json", "x-contract-version": "v2"},
    body: JSON.stringify(request)
  }).then(response => response.json());
}
