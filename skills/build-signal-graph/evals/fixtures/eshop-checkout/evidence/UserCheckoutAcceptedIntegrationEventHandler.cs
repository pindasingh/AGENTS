// Curated excerpt from Ordering.API/.../UserCheckoutAcceptedIntegrationEventHandler.cs (dev)
public class UserCheckoutAcceptedIntegrationEventHandler : IIntegrationEventHandler<UserCheckoutAcceptedIntegrationEvent> {
  public async Task Handle(UserCheckoutAcceptedIntegrationEvent @event) {
    if (@event.RequestId != Guid.Empty) {
      var command = new CreateOrderCommand(@event.Basket.Items, @event.UserId, @event.UserName /* payment/address fields */);
      await _mediator.Send(new IdentifiedCommand<CreateOrderCommand, bool>(command, @event.RequestId));
    }
  }
}
