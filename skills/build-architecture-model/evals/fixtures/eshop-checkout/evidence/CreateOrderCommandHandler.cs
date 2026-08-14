// Curated excerpt from Ordering.API/Application/Commands/CreateOrderCommandHandler.cs (dev)
public async Task<bool> Handle(CreateOrderCommand message, CancellationToken cancellationToken) {
  await _orderingIntegrationEventService.AddAndSaveEventAsync(new OrderStartedIntegrationEvent(message.UserId));
  var order = new Order(/* buyer, address, card metadata */);
  foreach (var item in message.OrderItems) order.AddOrderItem(/* item fields */);
  _orderRepository.Add(order);
  return await _orderRepository.UnitOfWork.SaveEntitiesAsync(cancellationToken);
}
