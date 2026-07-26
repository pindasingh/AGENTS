describe('authorized happy paths', () => {
  it('returns an invoice to an authenticated user', async () => {
    await requestAs('alice').get('/api/invoices/invoice-alice').expect(200);
  });

  it('allows an administrator to approve a refund', async () => {
    await requestAs('admin').post('/api/refunds/refund-1/approve').expect(200);
  });
});

// There are no anonymous, peer, cross-tenant, lower-role, post-logout,
// alternate-method, duplicate-parameter, CORS, or GraphQL negative tests.
