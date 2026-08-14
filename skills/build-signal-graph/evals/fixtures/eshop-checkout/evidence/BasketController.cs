// Curated excerpt from src/Services/Basket/Basket.API/Controllers/BasketController.cs (dev)
[Route("api/v1/[controller]")]
public class BasketController : ControllerBase {
  [Route("checkout")]
  [HttpPost]
  [ProducesResponseType((int)HttpStatusCode.Accepted)]
  public async Task<IActionResult> CheckoutAsync(BasketCheckout basketCheckout, [FromHeader(Name = "x-requestid")] string requestId) {
    var basket = await _repository.GetBasketAsync(_identityService.GetUserIdentity());
    if (basket == null) return BadRequest();
    var eventMessage = new UserCheckoutAcceptedIntegrationEvent(/* checkout, request id, basket */);
    _eventBus.Publish(eventMessage);
    return Accepted();
  }
}
