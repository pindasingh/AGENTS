[ApiController]
[Route("orders")]
public sealed class OrdersController(OrderReader orders) : ControllerBase
{
    [HttpGet("{orderId}")]
    [Authorize(Policy = "Orders.Read")]
    public async Task<OrderDto> Get(string orderId) => await orders.Find(orderId);
}

public sealed class OrderReader(OrdersDb db)
{
    public async Task<OrderDto> Find(string orderId)
    {
        var order = await db.Orders.SingleAsync(value => value.Id == orderId);
        return OrderDto.From(order);
    }
}
