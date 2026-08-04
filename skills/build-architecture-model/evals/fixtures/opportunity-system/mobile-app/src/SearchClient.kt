// Independently released mobile application.
class SearchClient {
  @POST("/api/opportunities/search")
  @Headers("X-Contract-Version: v2")
  suspend fun search(request: SearchRequestV2): SearchResponseV2
}
