export function register(app, store) {
  app.get("/api/orders/:id", requireUser, async (req, res) => {
    const order = await store.orders.findById(req.params.id);
    res.json(order);
  });

  app.post("/api/orders/:id/approve", requireUser, async (req, res) => {
    await store.orders.approve(req.params.id);
    res.status(204).end();
  });
}
